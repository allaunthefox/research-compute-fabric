#!/usr/bin/env bash
set -euo pipefail

# Hardened mail server bootstrap for Debian/Ubuntu or Arch/CachyOS hosts.
# Installs and configures: Postfix, Dovecot (IMAP/LMTP), OpenDKIM, TLS, fail2ban.
#
# Usage (run as root on the remote host):
#   sudo bash scripts/bootstrap_dag_mail_server.sh \
#     --mail-domain example.com \
#     --mail-host mail.example.com \
#     --admin-email admin@example.com

# Detect OS to choose appropriate package manager
detect_os() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "arch" || "$ID" == "cachyos" ]]; then
      echo "arch"
    elif [[ "$ID_LIKE" == *"arch"* ]]; then
      echo "arch"
    else
      echo "debian"
    fi
  else
    # Fallback: check for apt vs pacman
    if command -v pacman &>/dev/null; then
      echo "arch"
    else
      echo "debian"
    fi
  fi
}

OS_TYPE=$(detect_os)

install_packages() {
  if [ "$OS_TYPE" = "arch" ]; then
    pacman -Syu --noconfirm
    pacman -S --noconfirm \
      postfix dovecot \
      opendkim \
      certbot \
      fail2ban ufw
  else
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y \
      postfix postfix-pcre dovecot-core dovecot-imapd dovecot-lmtpd \
      opendkim opendkim-tools \
      certbot python3-certbot \
      fail2ban ufw
  fi
}

MAIL_DOMAIN=""
MAIL_HOST=""
ADMIN_EMAIL=""
MAIL_USER="vmail"
MAIL_UID="5000"
MAIL_GID="5000"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mail-domain)
      MAIL_DOMAIN="$2"; shift 2 ;;
    --mail-host)
      MAIL_HOST="$2"; shift 2 ;;
    --admin-email)
      ADMIN_EMAIL="$2"; shift 2 ;;
    --mail-user)
      MAIL_USER="$2"; shift 2 ;;
    --help)
      sed -n '1,40p' "$0"
      exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1 ;;
  esac
done

if [ -z "$MAIL_DOMAIN" ] || [ -z "$MAIL_HOST" ] || [ -z "$ADMIN_EMAIL" ]; then
  echo "Missing required args. Need --mail-domain, --mail-host, --admin-email" >&2
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

echo "[1/9] Detecting OS and installing packages..."
install_packages

echo "[2/9] Hostname and service accounts..."
hostnamectl set-hostname "$MAIL_HOST"
if ! getent group "$MAIL_USER" >/dev/null; then
  groupadd -g "$MAIL_GID" "$MAIL_USER"
fi
if ! id "$MAIL_USER" >/dev/null 2>&1; then
  useradd -g "$MAIL_USER" -u "$MAIL_UID" "$MAIL_USER" -d /var/mail/vhosts -m -s /usr/sbin/nologin
fi
mkdir -p /var/mail/vhosts
chown -R "$MAIL_USER":"$MAIL_USER" /var/mail/vhosts
chmod 770 /var/mail/vhosts

echo "[3/9] Postfix base config..."
postconf -e "myhostname = $MAIL_HOST"
postconf -e "mydomain = $MAIL_DOMAIN"
postconf -e "myorigin = $MAIL_DOMAIN"
postconf -e "mydestination = localhost"
postconf -e "inet_interfaces = all"
postconf -e "inet_protocols = all"
postconf -e "smtpd_banner = $MAIL_HOST ESMTP"
postconf -e "smtp_tls_security_level = may"
postconf -e "smtpd_tls_security_level = may"
postconf -e "smtpd_tls_auth_only = yes"
postconf -e "smtpd_tls_loglevel = 1"
postconf -e "smtpd_tls_received_header = yes"
postconf -e "virtual_transport = lmtp:unix:private/dovecot-lmtp"
postconf -e "virtual_mailbox_domains = $MAIL_DOMAIN"
postconf -e "virtual_mailbox_base = /var/mail/vhosts"
postconf -e "virtual_mailbox_maps = hash:/etc/postfix/vmailbox"
postconf -e "virtual_minimum_uid = $MAIL_UID"
postconf -e "virtual_uid_maps = static:$MAIL_UID"
postconf -e "virtual_gid_maps = static:$MAIL_GID"
postconf -e "smtpd_sasl_type = dovecot"
postconf -e "smtpd_sasl_path = private/auth"
postconf -e "smtpd_sasl_auth_enable = yes"
postconf -e "smtpd_recipient_restrictions = permit_sasl_authenticated,permit_mynetworks,reject_unauth_destination"
postconf -e "milter_default_action = accept"
postconf -e "milter_protocol = 6"
postconf -e "smtpd_milters = inet:127.0.0.1:8891"
postconf -e "non_smtpd_milters = inet:127.0.0.1:8891"

echo "[4/9] Postfix submission/smtps ports..."
if ! grep -q '^submission inet' /etc/postfix/master.cf; then
  cat >> /etc/postfix/master.cf <<'EOF'
submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_recipient_restrictions=permit_sasl_authenticated,reject

smtps     inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_recipient_restrictions=permit_sasl_authenticated,reject
EOF
fi

echo "[5/9] Dovecot config..."
mkdir -p /etc/dovecot/conf.d
cat > /etc/dovecot/conf.d/10-mail.conf <<EOF
mail_location = maildir:/var/mail/vhosts/%d/%n
first_valid_uid = $MAIL_UID
last_valid_uid = $MAIL_UID
mail_uid = $MAIL_UID
mail_gid = $MAIL_GID
EOF

cat > /etc/dovecot/conf.d/10-auth.conf <<'EOF'
disable_plaintext_auth = yes
auth_mechanisms = plain login
!include auth-passwdfile.conf.ext
EOF

cat > /etc/dovecot/conf.d/auth-passwdfile.conf.ext <<'EOF'
passdb {
  driver = passwd-file
  args = scheme=SHA512-CRYPT username_format=%u /etc/dovecot/users
}
userdb {
  driver = static
  args = uid=5000 gid=5000 home=/var/mail/vhosts/%d/%n
}
EOF

mkdir -p /etc/dovecot
if [ ! -f /etc/dovecot/users ]; then
  touch /etc/dovecot/users
  chmod 640 /etc/dovecot/users
fi
chown root:dovecot /etc/dovecot/users || true

cat > /etc/dovecot/conf.d/10-master.conf <<'EOF'
service lmtp {
  unix_listener /var/spool/postfix/private/dovecot-lmtp {
    mode = 0600
    user = postfix
    group = postfix
  }
}
service auth {
  unix_listener /var/spool/postfix/private/auth {
    mode = 0660
    user = postfix
    group = postfix
  }
}
EOF

echo "[6/9] OpenDKIM config and key generation..."
mkdir -p /etc/opendkim/keys/$MAIL_DOMAIN
if [ ! -f "/etc/opendkim/keys/$MAIL_DOMAIN/default.private" ]; then
  opendkim-genkey -D "/etc/opendkim/keys/$MAIL_DOMAIN" -d "$MAIL_DOMAIN" -s default || echo "WARNING: opendkim-genkey may have had issues"
fi
chown -R opendkim:opendkim /etc/opendkim/keys || true
chmod 750 /etc/opendkim/keys/$MAIL_DOMAIN || true
chmod 640 /etc/opendkim/keys/$MAIL_DOMAIN/default.private || true

# Ensure opendkim can read its config and keys
mkdir -p /etc/opendkim || true
chown -R opendkim:opendkim /etc/opendkim || true
chmod 755 /etc/opendkim || true

cat > /etc/opendkim.conf <<EOF
Syslog                  yes
UMask                   002
Canonicalization        relaxed/simple
Mode                    sv
SubDomains              no
AutoRestart             yes
AutoRestartRate         10/1h
Background              yes
DNSTimeout              5
SignatureAlgorithm      rsa-sha256
Socket                  inet:8891@127.0.0.1
UserID                  opendkim:opendkim
KeyTable                /etc/opendkim/key.table
SigningTable            refile:/etc/opendkim/signing.table
ExternalIgnoreList      /etc/opendkim/trusted.hosts
InternalHosts           /etc/opendkim/trusted.hosts
EOF

cat > /etc/opendkim/key.table <<EOF
default._domainkey.$MAIL_DOMAIN $MAIL_DOMAIN:default:/etc/opendkim/keys/$MAIL_DOMAIN/default.private
EOF

cat > /etc/opendkim/signing.table <<EOF
*@$MAIL_DOMAIN default._domainkey.$MAIL_DOMAIN
EOF

cat > /etc/opendkim/trusted.hosts <<EOF
127.0.0.1
localhost
$MAIL_HOST
EOF

echo "[7/9] TLS certificate (Let's Encrypt standalone or self-signed)..."
ufw allow 80/tcp || true

# Try Let's Encrypt for publicly resolvable domains
if ! certbot certonly --standalone --agree-tos --non-interactive -m "$ADMIN_EMAIL" -d "$MAIL_HOST" 2>/dev/null; then
  echo "WARNING: Let's Encrypt failed (domain may be Tailscale-only). Generating self-signed cert..."
  mkdir -p /etc/letsencrypt/live/"$MAIL_HOST"
  openssl req -x509 -newkey rsa:2048 -keyout /etc/letsencrypt/live/"$MAIL_HOST"/privkey.pem \
    -out /etc/letsencrypt/live/"$MAIL_HOST"/fullchain.pem -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=Org/CN=$MAIL_HOST" 2>/dev/null || {
    echo "ERROR: Could not create TLS certificate"
    exit 1
  }
fi

postconf -e "smtpd_tls_cert_file = /etc/letsencrypt/live/$MAIL_HOST/fullchain.pem"
postconf -e "smtpd_tls_key_file = /etc/letsencrypt/live/$MAIL_HOST/privkey.pem"
cat > /etc/dovecot/conf.d/10-ssl.conf <<EOF
ssl = required
ssl_cert = </etc/letsencrypt/live/$MAIL_HOST/fullchain.pem
ssl_key = </etc/letsencrypt/live/$MAIL_HOST/privkey.pem
EOF

echo "[8/9] Firewall + fail2ban..."
ufw allow 22/tcp || true
ufw allow 25/tcp || true
ufw allow 587/tcp || true
ufw allow 465/tcp || true
ufw allow 993/tcp || true
ufw --force enable

cat > /etc/fail2ban/jail.d/mail.conf <<'EOF'
[postfix]
enabled = true
port    = smtp,ssmtp,submission
logpath = /var/log/mail.log

[dovecot]
enabled = true
port    = pop3,pop3s,imap,imaps,submission,465,sieve
logpath = /var/log/mail.log
EOF

echo "[9/9] Enable services..."
systemctl enable opendkim postfix dovecot fail2ban || true
systemctl restart opendkim || echo "WARNING: opendkim restart failed (may need configuration)"
systemctl restart postfix || true
systemctl restart dovecot || true
systemctl restart fail2ban || true

echo ""
echo "Bootstrap complete."
echo ""
echo "Create mailbox credentials (example):"
echo "  doveadm pw -s SHA512-CRYPT"
echo "  # then add: user@$MAIL_DOMAIN:{SHA512-CRYPT}HASH" \
     "to /etc/dovecot/users and restart dovecot"
echo ""
echo "DNS records required:"
echo "  A     $MAIL_HOST -> <server-ip>"
echo "  MX    $MAIL_DOMAIN -> 10 $MAIL_HOST."
echo "  SPF   $MAIL_DOMAIN -> v=spf1 mx -all"
echo "  DKIM  default._domainkey.$MAIL_DOMAIN -> value from /etc/opendkim/keys/$MAIL_DOMAIN/default.txt"
echo "  DMARC _dmarc.$MAIL_DOMAIN -> v=DMARC1; p=quarantine; rua=mailto:postmaster@$MAIL_DOMAIN"
echo ""
echo "PTR (reverse DNS) should map server IP -> $MAIL_HOST (set at your VPS provider)."

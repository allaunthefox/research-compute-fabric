#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
NAME="${NAME:-research-stack-language-proof}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3a.large}"
VOLUME_SIZE="${VOLUME_SIZE:-100}"
KEY_NAME="${KEY_NAME:-research-stack-language-proof-20260525}"
LOCAL_PUBLIC_KEY="${LOCAL_PUBLIC_KEY:-$HOME/.ssh/id_ed25519.pub}"
LOCAL_PRIVATE_KEY="${LOCAL_PRIVATE_KEY:-$HOME/.ssh/id_ed25519}"
LOCAL_TOKEN_FILE="${LOCAL_TOKEN_FILE:-$HOME/.config/ene/language-proof-server.token}"
ALLOWED_TARGETS="${ALLOWED_TARGETS:-Semantics.FixedPoint,Semantics}"
LOCAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
USER_DATA="${LOCAL_ROOT}/4-Infrastructure/infra/aws_language_proof_server_user_data.sh"

if [ ! -s "$LOCAL_TOKEN_FILE" ]; then
  install -d -m 700 "$(dirname "$LOCAL_TOKEN_FILE")"
  umask 077
  python3 - <<'PY' >"$LOCAL_TOKEN_FILE"
import secrets
print(secrets.token_urlsafe(48))
PY
fi

if ! aws ec2 describe-key-pairs --region "$REGION" --key-names "$KEY_NAME" >/dev/null 2>&1; then
  aws ec2 import-key-pair \
    --region "$REGION" \
    --key-name "$KEY_NAME" \
    --public-key-material "fileb://${LOCAL_PUBLIC_KEY}" >/dev/null
fi

VPC_ID="$(aws ec2 describe-vpcs --region "$REGION" --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)"
SUBNET_ID="$(aws ec2 describe-subnets --region "$REGION" --filters Name=vpc-id,Values="$VPC_ID" Name=default-for-az,Values=true --query 'Subnets[0].SubnetId' --output text)"
AMI_ID="$(aws ssm get-parameter --region "$REGION" --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id --query 'Parameter.Value' --output text)"
CALLER_IP="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')"

SG_ID="$(aws ec2 describe-security-groups --region "$REGION" \
  --filters Name=group-name,Values="$NAME" Name=vpc-id,Values="$VPC_ID" \
  --query 'SecurityGroups[0].GroupId' --output text)"
if [ "$SG_ID" = "None" ]; then
  SG_ID="$(aws ec2 create-security-group --region "$REGION" \
    --group-name "$NAME" \
    --description "Research Stack dedicated language proof server" \
    --vpc-id "$VPC_ID" \
    --query 'GroupId' --output text)"
  aws ec2 create-tags --region "$REGION" --resources "$SG_ID" \
    --tags Key=Name,Value="$NAME" Key=Role,Value=language-proof-server >/dev/null
fi

for port in 22 8787; do
  aws ec2 authorize-security-group-ingress --region "$REGION" \
    --group-id "$SG_ID" --ip-permissions \
    "IpProtocol=tcp,FromPort=${port},ToPort=${port},IpRanges=[{CidrIp=${CALLER_IP}/32,Description=qfox-current-ip}]" \
    >/dev/null 2>&1 || true
done

INSTANCE_ID="$(aws ec2 describe-instances --region "$REGION" \
  --filters "Name=tag:Name,Values=$NAME" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)"

if [ "$INSTANCE_ID" = "None" ]; then
  INSTANCE_ID="$(aws ec2 run-instances --region "$REGION" \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --subnet-id "$SUBNET_ID" \
    --security-group-ids "$SG_ID" \
    --metadata-options HttpTokens=required,HttpEndpoint=enabled \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=${VOLUME_SIZE},VolumeType=gp3,DeleteOnTermination=true,Encrypted=true}" \
    --user-data "file://${USER_DATA}" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${NAME}},{Key=Role,Value=language-proof-server},{Key=Owner,Value=ResearchStack}]" \
    --query 'Instances[0].InstanceId' --output text)"
else
  STATE="$(aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].State.Name' --output text)"
  if [ "$STATE" = "stopped" ]; then
    aws ec2 start-instances --region "$REGION" --instance-ids "$INSTANCE_ID" >/dev/null
  fi
fi

aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-status-ok --region "$REGION" --instance-ids "$INSTANCE_ID"
PUBLIC_IP="$(aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"

SSH_OPTS=(-i "$LOCAL_PRIVATE_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
for _ in $(seq 1 40); do
  if ssh "${SSH_OPTS[@]}" "ubuntu@${PUBLIC_IP}" 'cloud-init status --wait >/dev/null && echo ready' >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

scp "${SSH_OPTS[@]}" "$LOCAL_TOKEN_FILE" "ubuntu@${PUBLIC_IP}:/tmp/language-proof-server.token"
ssh "${SSH_OPTS[@]}" "ubuntu@${PUBLIC_IP}" "sudo install -m 600 -o root -g root /tmp/language-proof-server.token /etc/language-proof-server/token && rm -f /tmp/language-proof-server.token && sudo tee /etc/language-proof-server/proof-server.env >/dev/null" <<ENV
PROOF_SERVER_TOKEN=$(cat "$LOCAL_TOKEN_FILE")
PROOF_ALLOWED_BUILD_TARGETS=${ALLOWED_TARGETS}
ENV

rsync -a --delete -e "ssh ${SSH_OPTS[*]}" --rsync-path="sudo rsync" \
  --exclude '.git/' \
  --exclude '.lake/build/' \
  --exclude 'lake-packages/*/.git/' \
  --exclude 'lake-packages/*/.lake/' \
  "${LOCAL_ROOT}/4-Infrastructure/infra/language_proof_server.py" \
  "ubuntu@${PUBLIC_IP}:/opt/language-proof-server/language_proof_server.py"

rsync -a --delete -e "ssh ${SSH_OPTS[*]}" --rsync-path="sudo rsync" \
  --exclude '.git/' \
  --exclude '.lake/build/' \
  --exclude 'lake-packages/*/.git/' \
  --exclude 'lake-packages/*/.lake/' \
  "${LOCAL_ROOT}/0-Core-Formalism" \
  "${LOCAL_ROOT}/2-Search-Space" \
  "ubuntu@${PUBLIC_IP}:/srv/research-stack/"

ssh "${SSH_OPTS[@]}" "ubuntu@${PUBLIC_IP}" "sudo tee /etc/systemd/system/language-proof-server.service >/dev/null" <<'UNIT'
[Unit]
Description=Research Stack Dedicated Language Proof Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=proofsrv
Group=proofsrv
WorkingDirectory=/opt/language-proof-server
EnvironmentFile=/etc/language-proof-server/proof-server.env
Environment=HOME=/var/lib/language-proof-server
Environment=PROOF_SERVER_HOST=0.0.0.0
Environment=PROOF_SERVER_PORT=8787
Environment=PROOF_REPO_DIR=/srv/research-stack
Environment=PROOF_LEAN_ROOT=0-Core-Formalism/lean/Semantics
Environment=PROOF_WORK_DIR=/var/lib/language-proof-server/work
Environment=PROOF_RECEIPT_DIR=/var/lib/language-proof-server/receipts
ExecStart=/usr/bin/python3 /opt/language-proof-server/language_proof_server.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/research-stack /var/lib/language-proof-server
CapabilityBoundingSet=
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
UNIT

ssh "${SSH_OPTS[@]}" "ubuntu@${PUBLIC_IP}" 'set -euxo pipefail
sudo chown -R proofsrv:proofsrv /opt/language-proof-server /srv/research-stack /var/lib/language-proof-server
sudo chmod 700 /etc/language-proof-server
sudo chmod 600 /etc/language-proof-server/token /etc/language-proof-server/proof-server.env
if [ ! -x /var/lib/language-proof-server/.elan/bin/elan ]; then
  sudo -u proofsrv -H sh -lc "curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none"
fi
sudo -u proofsrv -H sh -lc "cd /srv/research-stack/0-Core-Formalism/lean/Semantics && export PATH=/var/lib/language-proof-server/.elan/bin:\$PATH && elan toolchain install \"\$(cat lean-toolchain)\" && lake update"
sudo systemctl daemon-reload
sudo systemctl enable --now language-proof-server.service
sudo systemctl --no-pager --full status language-proof-server.service | sed -n "1,18p"
'

echo "INSTANCE_ID=${INSTANCE_ID}"
echo "PUBLIC_IP=${PUBLIC_IP}"
echo "PROOF_SERVER_URL=http://${PUBLIC_IP}:8787"
curl -fsS -H "Authorization: Bearer $(cat "$LOCAL_TOKEN_FILE")" "http://${PUBLIC_IP}:8787/health" | python3 -m json.tool

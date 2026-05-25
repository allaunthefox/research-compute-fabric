//! Error types for the NoDupeLabs ecosystem.
//!
//! Provides a typed error hierarchy using [`thiserror`] so that each
//! subsystem can be matched and handled independently.

/// Alias for `Result<T, nodupe_core::errors::Error>`.
pub type Result<T> = std::result::Result<T, Error>;

/// Root error type for all NoDupeLabs operations.
#[derive(Debug, thiserror::Error)]
pub enum Error {
    /// A security-related violation occurred.
    #[error("Security violation: {0}")]
    Security(String),

    /// An input validation failure.
    #[error("Validation error: {0}")]
    Validation(String),

    /// A tool execution error.
    #[error("Tool error: {0}")]
    Tool(String),

    /// A plugin error.
    #[error("Plugin error: {0}")]
    Plugin(String),

    /// A database-related failure.
    #[error("Database error: {0}")]
    Database(String),

    /// A resource limit was exceeded.
    #[error("Limit exceeded: {0}")]
    Limit(String),

    /// A configuration error (missing file, parse failure, etc.).
    #[error("Configuration error: {0}")]
    Config(String),

    /// An I/O error propagated from the standard library.
    #[error(transparent)]
    Io(#[from] std::io::Error),

    /// A TOML parsing error propagated from the `toml` crate.
    #[error(transparent)]
    Toml(#[from] toml::de::Error),

    /// A generic internal error wrapping a message.
    #[error("Internal error: {0}")]
    Internal(String),
}

impl Error {
    /// Create a new security error.
    pub fn security(msg: impl Into<String>) -> Self {
        Self::Security(msg.into())
    }

    /// Create a new validation error.
    pub fn validation(msg: impl Into<String>) -> Self {
        Self::Validation(msg.into())
    }

    /// Create a new tool error.
    pub fn tool(msg: impl Into<String>) -> Self {
        Self::Tool(msg.into())
    }

    /// Create a new plugin error.
    pub fn plugin(msg: impl Into<String>) -> Self {
        Self::Plugin(msg.into())
    }

    /// Create a new database error.
    pub fn database(msg: impl Into<String>) -> Self {
        Self::Database(msg.into())
    }

    /// Create a new limit error.
    pub fn limit(msg: impl Into<String>) -> Self {
        Self::Limit(msg.into())
    }

    /// Create a new configuration error.
    pub fn config(msg: impl Into<String>) -> Self {
        Self::Config(msg.into())
    }

    /// Create a new internal error.
    pub fn internal(msg: impl Into<String>) -> Self {
        Self::Internal(msg.into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn error_constructors() {
        let err = Error::security("access denied");
        assert_eq!(err.to_string(), "Security violation: access denied");

        let err = Error::validation("bad input");
        assert_eq!(err.to_string(), "Validation error: bad input");

        let err = Error::tool("tool crash");
        assert_eq!(err.to_string(), "Tool error: tool crash");

        let err = Error::plugin("plugin fail");
        assert_eq!(err.to_string(), "Plugin error: plugin fail");

        let err = Error::database("connection lost");
        assert_eq!(err.to_string(), "Database error: connection lost");

        let err = Error::limit("too many files");
        assert_eq!(err.to_string(), "Limit exceeded: too many files");

        let err = Error::config("file not found");
        assert_eq!(err.to_string(), "Configuration error: file not found");

        let err = Error::internal("unexpected state");
        assert_eq!(err.to_string(), "Internal error: unexpected state");
    }

    #[test]
    fn error_from_io() {
        let io_err = std::io::Error::new(std::io::ErrorKind::NotFound, "no such file");
        let err: Error = io_err.into();
        assert!(err.to_string().contains("no such file"));
    }

    #[test]
    fn error_from_toml() {
        let toml_err = "invalid table".parse::<toml::Value>().unwrap_err();
        let err: Error = toml_err.into();
        assert!(err.to_string().contains("invalid table"));
    }

    #[test]
    fn result_alias_works() {
        fn works() -> Result<i32> {
            Ok(42)
        }
        fn fails() -> Result<i32> {
            Err(Error::validation("nope"))
        }
        assert_eq!(works().unwrap(), 42);
        assert!(fails().is_err());
    }

    #[test]
    fn error_display_includes_variant() {
        let err = Error::limit("rate limit");
        let msg = err.to_string();
        assert!(msg.contains("rate limit"), "msg: {msg}");
    }

    #[test]
    fn error_debug_roundtrip() {
        let err = Error::database("disk full");
        let debug = format!("{err:?}");
        assert!(debug.contains("Database"));
        assert!(debug.contains("disk full"));
    }
}

// Logging service to reduce console noise in production
const isDev = import.meta.env.DEV;
const logLevel = import.meta.env.VITE_LOG_LEVEL || (isDev ? 'debug' : 'warn');

const LOG_LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  none: 4
};

const currentLogLevel = LOG_LEVELS[logLevel] || LOG_LEVELS.warn;

const logger = {
  debug: (message, ...args) => {
    if (currentLogLevel <= LOG_LEVELS.debug) {
      console.debug(`[DEBUG] ${message}`, ...args);
    }
  },

  info: (message, ...args) => {
    if (currentLogLevel <= LOG_LEVELS.info) {
      console.info(`[INFO] ${message}`, ...args);
    }
  },

  warn: (message, ...args) => {
    if (currentLogLevel <= LOG_LEVELS.warn) {
      console.warn(`[WARN] ${message}`, ...args);
    }
  },

  error: (message, ...args) => {
    if (currentLogLevel <= LOG_LEVELS.error) {
      console.error(`[ERROR] ${message}`, ...args);
    }
  }
};

// Export the logger
export default logger;

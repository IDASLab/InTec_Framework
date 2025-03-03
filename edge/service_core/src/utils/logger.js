const { createLogger, format, transports } = require("winston");
const path = require("path");

// Define log format
const logFormat = format.printf(({ level, message, timestamp }) => {
    return `${timestamp} [${level.toUpperCase()}]: ${message}`;
});

// Create logger
const logger = createLogger({
    level: "info",
    format: format.combine(format.timestamp(), logFormat),
    transports: [
        new transports.Console({ format: format.combine(format.colorize(), format.timestamp(), logFormat) }),
        new transports.File({ filename: path.join(__dirname, "../../logs/server.log"), level: "info" }),
        new transports.File({ filename: path.join(__dirname, "../../logs/error.log"), level: "error" })
    ]
});

module.exports = logger;


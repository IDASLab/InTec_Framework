const Sensor = require("../models/Sensor");
const logger = require("../utils/logger");

// 📌 GET: Welcome message at the root API
const getWelcomeMessage = (req, res) => {
    logger.info("API Request: Root Welcome Message");
    res.json({
        status: "success",
        message: "🚀 Welcome to Intec Framework! Your trusted API for managing sensor data.",
        documentation: "Visit https://intec-framework-docs.com for API usage details."
    });
};

// 📌 GET: Retrieve all unique sensor device names
const getAllSensorNames = async (req, res) => {
    try {
        logger.info("API Request: Fetching all unique sensor names");
        const sensorNames = await Sensor.distinct("device");
        if (!sensorNames.length) {
            logger.warn("No sensor devices found in the database.");
            return res.status(404).json({
                status: "info",
                message: "No sensor devices found in the database. Try adding some!"
            });
        }
        res.json({
            status: "success",
            message: `Found ${sensorNames.length} unique sensor devices.`,
            sensors: sensorNames
        });
    } catch (error) {
        logger.error(`Error fetching sensor names: ${error.message}`);
        res.status(500).json({
            status: "error",
            message: "Oops! Something went wrong while fetching sensor names.",
            error: error.message
        });
    }
};

// 📌 GET: Retrieve all data for a specific device
const getSensorByDevice = async (req, res) => {
    try {
        logger.info(`📡 API Request: Fetching data for device '${req.params.deviceName}'`);
        const sensors = await Sensor.find({ device: req.params.deviceName }).sort({ date: -1 });
        if (!sensors.length) {
            logger.warn(`No data found for device '${req.params.deviceName}'`);
            return res.status(404).json({
                status: "info",
                message: `ℹ️ No data found for device '${req.params.deviceName}'.`,
                suggestion: "Make sure the device ID is correct or try adding new sensor data."
            });
        }
        res.json({
            status: "success",
            message: `📡 Data retrieved for device '${req.params.deviceName}'.`,
            count: sensors.length,
            data: sensors
        });
    } catch (error) {
        logger.error(`Error fetching sensor data: ${error.message}`);
        res.status(500).json({
            status: "error",
            message: "An error occurred while fetching sensor data.",
            error: error.message
        });
    }
};

// 📌 GET: Retrieve the latest entry for a device
const getLatestSensorByDevice = async (req, res) => {
    try {
        logger.info(`API Request: Fetching latest data for device '${req.params.deviceName}'`);
        const sensor = await Sensor.findOne({ device: req.params.deviceName }).sort({ date: -1 });
        if (!sensor) {
            logger.warn(`No latest data found for device '${req.params.deviceName}'`);
            return res.status(404).json({
                status: "info",
                message: `🔍 No latest data found for device '${req.params.deviceName}'.`,
                suggestion: "Try checking another device or ensure data is being recorded."
            });
        }
        res.json({
            status: "success",
            message: `📡 Latest sensor data for device '${req.params.deviceName}' retrieved successfully.`,
            label: sensor.label,
            latency: sensor.latency,
            validation: sensor.validation,
            processed: sensor.processed,
            date: sensor.date
            
        });
    } catch (error) {
        logger.error(`Unable to fetch latest sensor data: ${error.message}`);
        res.status(500).json({
            status: "error",
            message: "⚠️ Unable to fetch the latest sensor data.",
            error: error.message
        });
    }
};

module.exports = { getWelcomeMessage, getAllSensorNames, getSensorByDevice, getLatestSensorByDevice };


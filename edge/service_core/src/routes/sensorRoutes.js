const express = require("express");
const {
    getWelcomeMessage,
    getAllSensorNames,
    getSensorByDevice,
    getLatestSensorByDevice
} = require("../controllers/sensorController");

const router = express.Router();

// 📌 GET: Welcome message at the root endpoint
router.get("/", getWelcomeMessage);

// 📌 GET: Retrieve all unique sensor device names
router.get("/sensors", getAllSensorNames);

// 📌 GET: Retrieve all data for a specific device
router.get("/sensors/:deviceName", getSensorByDevice);

// 📌 GET: Retrieve the latest entry for a device
router.get("/sensors/:deviceName/latest", getLatestSensorByDevice);

module.exports = router;


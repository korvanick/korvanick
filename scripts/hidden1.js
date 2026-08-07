// Your EIA API key (replace with your actual API key)
// Your EIA API key (replace with your actual API key)

// Your EIA API key (replace with your actual API key)
const EIA_API_KEY = "";  // TODO: load server-side, not from client JS

// Function to get the current date and time formatted to the required format
function getCurrentDate() {
    const now = new Date();
    
    // Round down to the nearest hour to get the most recent full hour
    now.setMinutes(0, 0, 0); // Set minutes, seconds, and milliseconds to 0

    // Format the date to YYYY-MM-DDTHH:mm:ss-05:00
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');  // Month is 0-indexed
    const day = now.getDate().toString().padStart(2, '0');  // Ensure day is 2 digits
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    const timezoneOffset = now.getTimezoneOffset(); // Get time zone offset in minutes
    const hoursOffset = Math.floor(Math.abs(timezoneOffset) / 60).toString().padStart(2, '0');
    const minutesOffset = (Math.abs(timezoneOffset) % 60).toString().padStart(2, '0');
    const timezone = (timezoneOffset > 0 ? '-' : '+') + hoursOffset + ':' + minutesOffset;

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${timezone}`;
}

const startDate = getCurrentDate();
const endDate = getCurrentDate();

console.log("Start Date:", startDate);
console.log("End Date:", endDate);

// Ensure that the startDate and endDate are valid strings
if (!startDate || !endDate) {
    console.error("Invalid date format");
}




/*
// Function to get the current date and time formatted to the required format
function getCurrentDate() {
    const now = new Date();
    
    // Round down to the nearest hour to get the most recent full hour
    now.setMinutes(0, 0, 0); // Set minutes, seconds, and milliseconds to 0

    // Format the date to YYYY-MM-DDTHH:mm:ss-05:00
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');  // Month is 0-indexed
    const day = now.getDate().toString().padStart(2, '0');  // Ensure day is 2 digits
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    const timezoneOffset = now.getTimezoneOffset(); // Get time zone offset in minutes
    const hoursOffset = Math.floor(Math.abs(timezoneOffset) / 60).toString().padStart(2, '0');
    const minutesOffset = (Math.abs(timezoneOffset) % 60).toString().padStart(2, '0');
    const timezone = (timezoneOffset > 0 ? '-' : '+') + hoursOffset + ':' + minutesOffset;

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${timezone}`;
}

const startDate = getCurrentDate();
const endDate = getCurrentDate();

console.log("Start Date:", startDate);
console.log("End Date:", endDate);

// Ensure that the startDate and endDate are valid strings
if (!startDate || !endDate) {
    console.error("Invalid date format");
}
*/
// Dynamically build the API URL using the startDate and endDate
const apiUrl = `https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/?frequency=local-hourly&data[0]=value&facets[respondent][]=NW&facets[fueltype][]=BAT&facets[fueltype][]=COL&facets[fueltype][]=GEO&facets[fueltype][]=NG&facets[fueltype][]=NUC&facets[fueltype][]=OIL&facets[fueltype][]=OTH&facets[fueltype][]=SNB&facets[fueltype][]=SUN&facets[fueltype][]=UNK&facets[fueltype][]=WAT&facets[fueltype][]=WND&start=${startDate}&end=${endDate}&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000&api_key=${apiKey}`;



fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
        // Log the full API response for inspection
        console.log("Full API Response:", data);  

        let output = "<h2>Energy Generation Data</h2>";

        // Initialize variables to store the totals for all generation and carbon-emitting generation
        let totalGeneration = 0;
        let carbonEmittingGeneration = 0;

        // Define the categories of fuel types
        const carbonEmittingFuelTypes = ["COL", "NG", "OIL", "OTH"];
        const carbonFreeFuelTypes = ["NUC", "WAT", "WND", "SUN", "GEO", "BAT"];

        // Check if the data contains the expected structure
        if (data && data.response && Array.isArray(data.response.data) && data.response.data.length > 0) {
            let generationData = data.response.data;
            output += "<ul>";

            // Loop through each item and accumulate generation values
            generationData.forEach(item => {
                console.log("Item:", item);  // Log each item to check its structure

                const period = item.period;  // Period (timestamp)
                let value = item.value;    // Value (generation amount in MW)
                const respondent = item["respondent-name"];  // Region name
                const fuelType = item.fueltype;  // Fuel type

                // Ensure the value is a valid number
                value = parseFloat(value);

                // Check if value is valid (non-null, non-undefined, and a number)
                if (!isNaN(value)) {
                    // Add to total generation
                    totalGeneration += value;

                    // Add to carbon-emitting generation if the fuel type is carbon-emitting
                    if (carbonEmittingFuelTypes.includes(fuelType)) {
                        carbonEmittingGeneration += value;
                    }
                } else {
                    console.warn("Skipping invalid value for item:", item);  // Warn if value is invalid
                }

                // Only include the item if the value is valid
                if (!isNaN(value)) {
                    output += `<li>
                                <strong>Period:</strong> ${period} <br>
                                <strong>Fuel Type:</strong> ${fuelType} <br>
                                <strong>Region:</strong> ${respondent} <br>
                                <strong>Generation Value:</strong> ${value} MW
                                </li>`;
                }
            });
            output += "</ul>";

            // Ensure totalGeneration is a valid number and perform the percentage calculation
            if (totalGeneration > 0) {
                let carbonEmittingPercentage = (carbonEmittingGeneration / totalGeneration) * 100;

                // Add the summary to the output
                output += `<h3>Total Generation: ${totalGeneration.toFixed(2)} MW</h3>`;
                output += `<h3>Carbon-Emitting Generation: ${carbonEmittingGeneration.toFixed(2)} MW</h3>`;
                output += `<h3>Percentage of Generation from Carbon-Emitting Resources: ${carbonEmittingPercentage.toFixed(2)}%</h3>`;
            } else {
                output += "<p>No valid generation data available.</p>";
            }
        } else {
            output += "<p>No data available.</p>";
        }

        // Display the output on the webpage in the "energyData" div
        document.getElementById('energyData').innerHTML = output;
    })
    .catch(error => {
        console.error('Error fetching data:', error);
        document.getElementById('energyData').innerHTML = '<p>Sorry, there was an error loading the data.</p>';
    });



import express from 'express';
import { exec } from 'child_process';

const router = express.Router();

// Helper to run the Python script
const runPythonScript = (url) => {
  const command = `python3 /app/python_scripts/scrape_links.py "${url}"`;
  console.log(`[LOG]: Starting Python script with command: ${command}`); // Log the Python command

  return new Promise((resolve, reject) => {
    const startTime = Date.now(); // Track execution time

    const child = exec(command, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
      const duration = ((Date.now() - startTime) / 1000).toFixed(2); // Calculate script execution time
      console.log(`[LOG]: Python script execution completed in ${duration} seconds.`);

      if (error) {
        console.error(`[ERROR]: Python execution failed: ${error.message}`);
        return reject(new Error(`Python execution error: ${error.message}`));
      }

      if (stderr && !stderr.includes('[WDM]')) { // Ignore WebDriver logs
        console.warn(`[WARN]: Python script stderr: ${stderr}`);
        return reject(new Error(`Python stderr: ${stderr}`));
      }

      try {
        console.log(`[LOG]: Raw Python script output:\n${stdout}`); // Log raw Python output
        const result = JSON.parse(stdout); // Parse JSON response
        console.log(`[LOG]: Parsed Python script output:`, result);
        resolve(result);
      } catch (err) {
        console.error(`[ERROR]: Failed to parse Python output.`, err.message);
        reject(new Error(`Error parsing Python output: ${err.message}`));
      }
    });
  });
};

// Helper to recursively process scraped data into the required format
const processScrapedData = (data, visitedUrls = new Set()) => {
  console.log(`[LOG]: Processing scraped data recursively.`);

  const cleanLink = (url) => url.replace('/panorama', '');

  const processLinks = (links) => {
    if (!Array.isArray(links)) {
      console.warn(`[WARN]: Invalid links data structure received. Expected an array.`);
      return [];
    }

    return links
      .filter(link => link.url && !visitedUrls.has(cleanLink(link.url))) // Skip invalid or already visited links
      .map(link => {
        const processedLink = {
          url: cleanLink(link.url),
          title: link.content?.title || 'No title available',
          embedded_links: processLinks(link.links || []), // Recursively process embedded links
        };
        visitedUrls.add(processedLink.url);
        return processedLink;
      });
  };

  return {
    url: cleanLink(data.url || 'No URL available'),
    additionalData: {
      title: data.content?.title || 'No title available',
      content: data.content?.summary || 'No content available',
    },
    links: processLinks(data.links || []),
  };
};

// API route for scraping
router.post('/', async (req, res) => {
  const { url } = req.body;

  console.log(`[LOG]: Received POST request to scrape URL: ${url}`);

  if (!url || typeof url !== 'string' || !url.startsWith('http')) {
    console.error(`[ERROR]: Invalid or missing URL: ${url}`);
    return res.status(400).json({ error: 'Invalid or missing URL' });
  }

  try {
    console.log(`[LOG]: Invoking Python script to scrape the URL.`);
    const scrapeResult = await runPythonScript(url);

    console.log(`[LOG]: Scraping complete. Processing scraped data.`);
    const processedData = processScrapedData(scrapeResult);

    console.log(`[LOG]: Scraping and processing complete. Sending response to client.`);
    res.status(200).json({
      message: 'Scraping complete',
      result: processedData,
    });
  } catch (error) {
    console.error(`[ERROR]: Scraping failed: ${error.message}`);
    res.status(500).json({ error: error.message });
  }
});

export default router;

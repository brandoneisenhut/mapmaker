import logging

# Configure logging at the very start of the script
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Output test logging messages
logging.debug("Debug message: Starting the script")
try:
    logging.info("Info message: Performing an operation")
    
    # Simulate an operation
    result = 10 / 2
    logging.debug(f"Debug message: Operation result is {result}")
    
    # Simulate an error
    # Uncomment the next line to test error logging
    # error_result = 10 / 0
    
    logging.info("Info message: Script completed successfully")

except Exception as e:
    logging.error(f"Error message: An exception occurred: {e}")

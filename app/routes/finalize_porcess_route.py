import pandas as pd
from io import StringIO
from fastapi import APIRouter, BackgroundTasks
from app.services import blob_service
from app.services import email_service
from app.logFile import logger



finalize_process_router = APIRouter(prefix="/finalize")


platforms = ["apec", "indeed", "jungle", "hellowork", "linkedin"]
#platforms = ["apec", "indeed", "jungle", "hellowork"]
regions = ["france"]

async def transfer_summarize_csv():
# Calculate total line count and determine success status
    line_counts = {}  
    transfer_status = {}
    for platform in platforms:
        transfer_status[platform] = {}
        line_counts[platform] = {}
        for region in regions:
            blob_path = f"temp/summarize/{platform}/{region}.csv"
            transfer_success = False
            lines = 0
            try:
                # Retrieve CSV content from blob
                csv_content = blob_service.get_csv_content(blob_path)
                
                # Count the number of lines in the CSV content
                df = pd.read_csv(StringIO(csv_content))
                lines = df.shape[0]

                # Finalize the summarize process
                transfer_success = blob_service.finalize_summarize_process(platform, region) 
                                
            except Exception as e:
                logger.exception(f"Could not get line count for {blob_path}")

            # Update status and line counts
            transfer_status[platform][region] = transfer_success
            line_counts[platform][region] = lines
    
    # Check if all transfers were successful
    success = all(
        all(status for status in platform_status.values())
        for platform_status in transfer_status.values()
    )

    # Send notification email
    email_service.send_job_notification(line_counts, transfer_status, success)
    
    return {
        "line_counts": line_counts,
        "transfer_status": transfer_status,
        "overall_success": success
    }

async def transfert_model_data():
    # Track transfer status for each platform and region
    transfer_status = {}
    
    for platform in platforms:
        transfer_status[platform] = {}
        for region in regions:
            try:
                # Attempt to transfer model data
                success = blob_service.finalize_model_data_transfer(platform, region)
                transfer_status[platform][region] = success
                
                if success:
                    logger.info(f"Successfully transferred model data for {platform} - {region}")
                else:
                    logger.warning(f"Failed to transfer model data for {platform} - {region}")
                    
            except Exception as e:
                logger.exception(f"Error transferring model data for {platform} - {region}")
                transfer_status[platform][region] = False
    
    # Check if all transfers were successful
    overall_success = all(
        all(status for status in platform_status.values())
        for platform_status in transfer_status.values()
    )
    
    return {
        "transfer_status": transfer_status,
        "overall_success": overall_success
    }

async def transfer_summarize_and_models():
    """Performs the transfer of summaries and models without returning any result."""
    try:
        # Transfer summaries
        logger.info("Starting summary transfer.")
        await transfer_summarize_csv()

        # Transfer models
        logger.info("Starting model transfer.")
        await transfert_model_data()

        logger.info("Summary and model transfers completed successfully.")
    except Exception as e:
        logger.error(f"Error during summary and model transfer: {str(e)}")


@finalize_process_router.post("/transfer-summarize")
async def transfer_summarize():
    """
    Backup route to manually trigger the transfer of summary data for all platforms and regions.
    This route ensures that the summary data is successfully transferred for each platform and region,
    and returns an overall success status along with individual transfer statuses.
    It serves as a fallback in case the scheduled task didn't work as expected.
    """
    return await transfer_summarize_csv()

@finalize_process_router.post("/transfer-models")
async def transfer_models():
    """
    Backup route to manually trigger the transfer of model data for all platforms and regions.
    This route ensures that the model data is successfully transferred for each platform and region,
    and returns an overall success status along with individual transfer statuses.
    It serves as a fallback in case the scheduled task didn't work as expected.
    """
    return await transfert_model_data()


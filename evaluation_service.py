"""
Evaluation service for submitting results to the evaluation endpoint.
Implements retry logic with exponential backoff.
"""
import httpx
import asyncio
import logging
from typing import Dict

logger = logging.getLogger(__name__)


async def submit_evaluation(evaluation_url: str, data: Dict) -> None:
    """
    POSTs evaluation data to the evaluation_url with retry logic.
    
    Args:
        evaluation_url: URL to POST results to
        data: Dictionary containing evaluation data
    """
    max_retries = 5
    backoff_delays = [1, 2, 4, 8, 16]  # seconds
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries):
            try:
                logger.info(f"Submitting evaluation (attempt {attempt + 1}/{max_retries})")
                logger.info(f"POST to: {evaluation_url}")
                logger.info(f"Data: {data}")
                
                response = await client.post(evaluation_url, json=data)
                
                if response.status_code == 200:
                    logger.info("Evaluation submitted successfully")
                    return
                else:
                    logger.warning(
                        f"Evaluation submission failed with status {response.status_code}: "
                        f"{response.text}"
                    )
                    
            except Exception as e:
                logger.error(f"Error submitting evaluation: {str(e)}")
            
            # If not the last attempt, wait before retrying
            if attempt < max_retries - 1:
                delay = backoff_delays[attempt]
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        logger.error(f"Failed to submit evaluation after {max_retries} attempts")
        raise Exception(f"Failed to submit evaluation to {evaluation_url} after {max_retries} retries")
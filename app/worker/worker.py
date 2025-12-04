import asyncio
from loguru import logger
from app.core import globals
from app.ml.buffer import RingBuffer
from app.ml.features import FeatureExtractor
from app.ml.model import ModelWrapper
from app.worker.batcher import BatchWriter

async def process_gsi_stream():
    """
    Continuous loop that consumes from the global queue and processes GSI data.
    """
    logger.info("Worker started: Waiting for GSI data...")
    
    try:
        # Initialize ML components
        ring_buffer = RingBuffer(max_len=30) # 30 ticks ~ 3-10 seconds depending on rate
        feature_extractor = FeatureExtractor()
        model = ModelWrapper()
        batcher = BatchWriter(flush_interval=1)
        logger.info("Worker: ML components initialized")
    except Exception as e:
        logger.error(f"Worker initialization failed: {e}")
        return
    
    logger.info(f"Worker: Queue ID: {id(globals.queue)}")
    
    while True:
        try:
            # 1. Get GSI data from Queue
            gsi_data = await globals.queue.get()
            logger.info(f"Worker: Received GSI data. Queue size: {globals.queue.qsize()}")
            
            # 2. Add to Ring Buffer (Smoothing & Deduplication)
            added = ring_buffer.add_tick(gsi_data)
            logger.info(f"Worker: Added to buffer? {added}")
            
            # 3. Get Smoothed State
            smoothed_tick = ring_buffer.get_smoothed_features()
            logger.info(f"Worker: Smoothed tick present? {smoothed_tick is not None}")
            
            if smoothed_tick:
                # Extract Features
                features = feature_extractor.extract(smoothed_tick)
                logger.info(f"Worker: Features extracted: {features}")
                
                # 4. Predict Win Probability
                win_prob = model.predict(features)
                logger.info(f"Worker: Prediction: {win_prob}")
                
                # 5. Log Result (Simulating "Live" output)
                timestamp = smoothed_tick.get('map', {}).get('clock_time', 'Unknown')
                logger.info(f"Tick: {timestamp} | Win Prob: {win_prob:.4f}")

                # 6. Broadcast to WebSockets
                from app.core.websockets import manager
                await manager.broadcast({
                    "type": "update",
                    "timestamp": timestamp,
                    "win_probability": win_prob,
                    "features": features
                })
                
                # 7. Batch Write to DB
                await batcher.add_tick(smoothed_tick, win_prob)
                
            globals.queue.task_done()
            
        except asyncio.CancelledError:
            logger.info("Worker task cancelled")
            # Flush remaining ticks
            await batcher.flush()
            break
        except Exception as e:
            logger.error(f"Error processing GSI data: {e}")

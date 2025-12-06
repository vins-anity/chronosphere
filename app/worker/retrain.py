import asyncio
from datetime import datetime, time
import random
from typing import Optional
from loguru import logger

from app.ml.collect import OpenDotaCollector
from app.ml.incremental import IncrementalTrainer
from app.ml.versioning import version_manager
from app.core import globals

class AutoRetrainer:
    """
    Zero-Touch Automated Retraining Service.
    
    Responsibilities:
    1. Daily Check: Wake up (default 04:00 UTC).
    2. Catch Up: Fetch ALL new pro matches since last training.
    3. Train: Create a candidate model.
    4. Gate: Compare candidate vs current model.
    5. Promote: Hot-swap if candidate is better.
    """
    
    def __init__(self):
        self.collector = OpenDotaCollector()
        self.trainer = IncrementalTrainer()
        self.is_running = False
        
    async def start_loop(self):
        """Start the background scheduling loop."""
        logger.info("AutoML: Service started. Schedule: Daily at 04:00 UTC")
        
        while True:
            try:
                now = datetime.utcnow()
                # Target: 04:00 UTC (Low traffic time)
                target = now.replace(hour=4, minute=0, second=0, microsecond=0)
                
                if now >= target:
                    # If passed today, schedule for tomorrow
                    target = target.replace(day=now.day + 1)
                
                wait_seconds = (target - now).total_seconds()
                logger.info(f"AutoML: Sleeping for {wait_seconds / 3600:.1f} hours until next cycle")
                
                # Sleep until scheduled time
                await asyncio.sleep(wait_seconds)
                
                # Run Cycle
                await self.run_daily_cycle()
                
            except asyncio.CancelledError:
                logger.info("AutoML: Service cancelled")
                break
            except Exception as e:
                logger.error(f"AutoML: Loop error: {e}")
                await asyncio.sleep(60) # Prevent tight loop on error

    async def run_daily_cycle(self):
        """Run the full ingestion and training cycle."""
        if self.is_running:
            logger.warning("AutoML: Cycle already running, skipping")
            return
            
        self.is_running = True
        logger.info("AutoML: 🔄 Starting Daily Cycle")
        
        try:
            # 1. Catch Up Data
            # "Ingest EVERYTHING since last sync"
            last_id = self.trainer.last_match_id
            limit = 200 # Aggressive daily limit (covers even busy tournament days)
            
            # Since we can't easily query "since match_id" on OpenDota ProMatches directly without pagination,
            # we rely on the collector's "quick" mode or our own custom logic.
            # However, OpenDotaCollector.fetch_pro_matches fetches *most recent*.
            # If we fetch 200, we likely overlap. The trainer handles dedup.
            
            logger.info("AutoML: Fetching new matches...")
            new_matches = await self.collector.fetch_pro_matches(limit=limit)
            
            # Process & Save
            # We need to process them into training rows (this fetches details)
            # This consumes strict API quota (1 call per match)
            training_rows = []
            processed_count = 0
            
            for match in new_matches:
                match_id = match.get("match_id")
                # Skip if already have this match (Optimization: Check sync state first)
                if last_id and match_id <= last_id:
                    continue
                    
                details = await self.collector.fetch_match_details(match_id)
                if details:
                    rows = self.collector._process_match_enhanced(details)
                    training_rows.extend(rows)
                    processed_count += 1
                    
                # Rate limit safety sleep
                await asyncio.sleep(1.0) 
            
            if not training_rows:
                logger.info("AutoML: No new matches found to train on.")
                return

            logger.info(f"AutoML: Ingested {len(training_rows)} new training rows from {processed_count} matches.")
            
            # 2. Append to Dataset
            added = self.trainer.append_training_data(training_rows)
            if added == 0:
                logger.info("AutoML: Data was duplicate. Skipping training.")
                return

            # 3. Train Candidate
            logger.info("AutoML: 🏋️ Training Candidate Model...")
            result = self.trainer.train_incremental(
                patch="7.39e", # Dynamic patch detection could be added here
                continue_from=version_manager.current_version
            )
            
            candidate_version = result['version']
            candidate_metrics = result['metrics']
            
            # 4. Evaluation Gate
            current_meta = version_manager.get_current_model_metadata()
            
            promote = False
            if not current_meta:
                logger.info("AutoML: No current model. Promotion Automatic.")
                promote = True
            else:
                current_auc = current_meta.metrics.get('auc', 0.5)
                candidate_auc = candidate_metrics.get('auc', 0.5)
                
                # Allow tiny regression (-0.005) if sample size grows significantly, 
                # but generally demand parity or improvement.
                logger.info(f"AutoML Gate: Candidate AUC {candidate_auc:.4f} vs Current {current_auc:.4f}")
                
                if candidate_auc >= current_auc - 0.005:
                    promote = True
                else:
                    logger.warning("AutoML: Candidate rejected (Performance regression).")

            # 5. Promotion
            if promote:
                version_manager.set_current(candidate_version)
                logger.info(f"AutoML: 🚀 PROMOTED v{candidate_version} to Live!")
            
        except Exception as e:
            logger.error(f"AutoML: Cycle failed: {e}")
        finally:
            self.is_running = False

# Singleton
auto_retrainer = AutoRetrainer()

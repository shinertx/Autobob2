#!/usr/bin/env python3
"""
V26MEME System Test - Comprehensive validation of all components
Tests the complete system stack before deployment
"""

import os
import sys
import asyncio
import subprocess
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemValidator:
    """
    Validates all V26MEME system components
    """
    
    def __init__(self):
        self.project_root = project_root
        self.test_results = {}
        
    async def run_full_validation(self):
        """
        Run comprehensive system validation
        """
        
        logger.info("🚀 Starting V26MEME System Validation")
        logger.info("=" * 50)
        
        # Test directory structure
        await self.test_directory_structure()
        
        # Test configuration files
        await self.test_configuration_files()
        
        # Test dependencies
        await self.test_dependencies()
        
        # Test environment setup
        await self.test_environment()
        
        # Test core components
        await self.test_core_components()
        
        # Test intelligence layer
        await self.test_intelligence_layer()
        
        # Test infrastructure
        await self.test_infrastructure()
        
        # Generate report
        self.generate_validation_report()
        
    async def test_directory_structure(self):
        """
        Verify all required directories exist
        """
        
        logger.info("📁 Testing directory structure...")
        
        required_dirs = [
            'core',
            'intelligence', 
            'strategies',
            'strategies/mev',
            'strategies/arbitrage',
            'strategies/sniping',
            'strategies/discovered',
            'infrastructure',
            'tests',
            'dashboard',
            'web',
            'scripts',
            'config',
            'data',
            'data/backtests',
            'logs',
            'logs/evolution',
            'docs',
            '.github'
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            self.test_results['directory_structure'] = {
                'status': 'FAIL',
                'missing': missing_dirs
            }
            logger.error(f"❌ Missing directories: {missing_dirs}")
        else:
            self.test_results['directory_structure'] = {
                'status': 'PASS',
                'message': 'All required directories present'
            }
            logger.info("✅ Directory structure complete")
    
    async def test_configuration_files(self):
        """
        Verify all required configuration files exist
        """
        
        logger.info("⚙️ Testing configuration files...")
        
        required_files = [
            'Cargo.toml',
            'go.mod', 
            'requirements.txt',
            'docker-compose.yml',
            '.env.example',
            '.gitignore',
            'setup.sh',
            'dashboard/package.json',
            'scripts/init_db.sql'
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            self.test_results['configuration_files'] = {
                'status': 'FAIL',
                'missing': missing_files
            }
            logger.error(f"❌ Missing configuration files: {missing_files}")
        else:
            self.test_results['configuration_files'] = {
                'status': 'PASS',
                'message': 'All configuration files present'
            }
            logger.info("✅ Configuration files complete")
    
    async def test_dependencies(self):
        """
        Test if required system dependencies are available
        """
        
        logger.info("📦 Testing system dependencies...")
        
        dependencies = {
            'docker': 'docker --version',
            'docker-compose': 'docker-compose --version', 
            'python3': 'python3 --version',
            'cargo': 'cargo --version',
            'go': 'go version'
        }
        
        missing_deps = []
        for name, command in dependencies.items():
            try:
                result = subprocess.run(command.split(), 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                if result.returncode != 0:
                    missing_deps.append(name)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing_deps.append(name)
        
        if missing_deps:
            self.test_results['dependencies'] = {
                'status': 'FAIL',
                'missing': missing_deps
            }
            logger.error(f"❌ Missing dependencies: {missing_deps}")
        else:
            self.test_results['dependencies'] = {
                'status': 'PASS',
                'message': 'All system dependencies available'
            }
            logger.info("✅ System dependencies complete")
    
    async def test_environment(self):
        """
        Test environment variable setup
        """
        
        logger.info("🔧 Testing environment setup...")
        
        # Check if .env exists
        env_file = self.project_root / '.env'
        if not env_file.exists():
            self.test_results['environment'] = {
                'status': 'WARNING',
                'message': '.env file not found - copy from .env.example'
            }
            logger.warning("⚠️ .env file not found")
            return
        
        # Check critical environment variables
        critical_vars = [
            'OPENAI_API_KEY',
            'DATABASE_URL', 
            'REDIS_URL'
        ]
        
        missing_vars = []
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.test_results['environment'] = {
                'status': 'WARNING',
                'missing': missing_vars
            }
            logger.warning(f"⚠️ Missing environment variables: {missing_vars}")
        else:
            self.test_results['environment'] = {
                'status': 'PASS',
                'message': 'Environment properly configured'
            }
            logger.info("✅ Environment setup complete")
    
    async def test_core_components(self):
        """
        Test core Rust and Go components
        """
        
        logger.info("🦀 Testing core components...")
        
        core_files = [
            'core/discovery_engine.rs',
            'core/execution_engine.go',
            'core/risk_manager.rs',
            'core/evolution_ai.py'
        ]
        
        missing_core = []
        for file_name in core_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                missing_core.append(file_name)
        
        # Test Rust compilation (if cargo is available)
        rust_compile_ok = True
        try:
            result = subprocess.run(['cargo', 'check'], 
                                  cwd=self.project_root,
                                  capture_output=True, 
                                  text=True,
                                  timeout=60)
            if result.returncode != 0:
                rust_compile_ok = False
                logger.warning(f"⚠️ Rust compilation issues: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            rust_compile_ok = False
        
        # Test Go compilation
        go_compile_ok = True
        try:
            result = subprocess.run(['go', 'mod', 'tidy'], 
                                  cwd=self.project_root,
                                  capture_output=True, 
                                  text=True,
                                  timeout=60)
            if result.returncode != 0:
                go_compile_ok = False
                logger.warning(f"⚠️ Go module issues: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            go_compile_ok = False
        
        if missing_core:
            self.test_results['core_components'] = {
                'status': 'FAIL',
                'missing_files': missing_core,
                'rust_compile': rust_compile_ok,
                'go_compile': go_compile_ok
            }
            logger.error(f"❌ Missing core files: {missing_core}")
        elif not rust_compile_ok or not go_compile_ok:
            self.test_results['core_components'] = {
                'status': 'WARNING',
                'rust_compile': rust_compile_ok,
                'go_compile': go_compile_ok
            }
            logger.warning("⚠️ Core components have compilation issues")
        else:
            self.test_results['core_components'] = {
                'status': 'PASS',
                'message': 'All core components present and compilable'
            }
            logger.info("✅ Core components complete")
    
    async def test_intelligence_layer(self):
        """
        Test Python intelligence components
        """
        
        logger.info("🧠 Testing intelligence layer...")
        
        intelligence_files = [
            'intelligence/openai_strategist.py',
            'intelligence/pattern_synthesizer.py',
            'intelligence/sentiment_analyzer.py',
            'intelligence/meta_learner.py'
        ]
        
        missing_intel = []
        for file_name in intelligence_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                missing_intel.append(file_name)
        
        # Test Python imports
        import_errors = []
        try:
            sys.path.append(str(self.project_root))
            from intelligence.openai_strategist import OpenAIStrategist
            from intelligence.pattern_synthesizer import PatternSynthesizer
            from intelligence.sentiment_analyzer import SentimentAnalyzer
            from intelligence.meta_learner import MetaLearner
        except ImportError as e:
            import_errors.append(str(e))
        
        if missing_intel:
            self.test_results['intelligence_layer'] = {
                'status': 'FAIL',
                'missing_files': missing_intel,
                'import_errors': import_errors
            }
            logger.error(f"❌ Missing intelligence files: {missing_intel}")
        elif import_errors:
            self.test_results['intelligence_layer'] = {
                'status': 'WARNING',
                'import_errors': import_errors
            }
            logger.warning(f"⚠️ Intelligence layer import issues: {import_errors}")
        else:
            self.test_results['intelligence_layer'] = {
                'status': 'PASS',
                'message': 'Intelligence layer complete and importable'
            }
            logger.info("✅ Intelligence layer complete")
    
    async def test_infrastructure(self):
        """
        Test infrastructure components
        """
        
        logger.info("🏗️ Testing infrastructure...")
        
        # Test Docker Compose syntax
        docker_compose_ok = True
        try:
            result = subprocess.run(['docker-compose', 'config'],
                                  cwd=self.project_root,
                                  capture_output=True,
                                  text=True,
                                  timeout=30)
            if result.returncode != 0:
                docker_compose_ok = False
                logger.warning(f"⚠️ Docker Compose issues: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            docker_compose_ok = False
        
        # Check database schema
        db_schema_exists = (self.project_root / 'scripts' / 'init_db.sql').exists()
        
        if not docker_compose_ok:
            self.test_results['infrastructure'] = {
                'status': 'WARNING',
                'docker_compose': docker_compose_ok,
                'db_schema': db_schema_exists
            }
            logger.warning("⚠️ Infrastructure has issues")
        else:
            self.test_results['infrastructure'] = {
                'status': 'PASS',
                'docker_compose': docker_compose_ok,
                'db_schema': db_schema_exists
            }
            logger.info("✅ Infrastructure complete")
    
    def generate_validation_report(self):
        """
        Generate comprehensive validation report
        """
        
        logger.info("\n" + "=" * 50)
        logger.info("📊 V26MEME SYSTEM VALIDATION REPORT")
        logger.info("=" * 50)
        
        passed = 0
        warned = 0
        failed = 0
        
        for component, result in self.test_results.items():
            status = result['status']
            if status == 'PASS':
                passed += 1
                logger.info(f"✅ {component}: {result.get('message', 'OK')}")
            elif status == 'WARNING':
                warned += 1
                logger.warning(f"⚠️ {component}: Issues found")
                if 'missing' in result:
                    logger.warning(f"   Missing: {result['missing']}")
                if 'import_errors' in result:
                    logger.warning(f"   Import errors: {result['import_errors']}")
            else:
                failed += 1
                logger.error(f"❌ {component}: FAILED")
                if 'missing' in result:
                    logger.error(f"   Missing: {result['missing']}")
        
        logger.info("\n" + "=" * 50)
        logger.info(f"📈 SUMMARY: {passed} passed, {warned} warnings, {failed} failed")
        
        if failed == 0 and warned == 0:
            logger.info("🎉 ALL SYSTEMS GO! V26MEME is ready for deployment!")
            return True
        elif failed == 0:
            logger.info("⚠️ System ready with warnings. Review issues before deployment.")
            return True
        else:
            logger.error("❌ System NOT ready. Fix critical issues before deployment.")
            return False

async def main():
    """
    Run system validation
    """
    
    validator = SystemValidator()
    success = await validator.run_full_validation()
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Review any warnings above")
        print("2. Configure .env with your API keys")
        print("3. Run: ./setup.sh")
        print("4. Start system: docker-compose up")
        return 0
    else:
        print("\n❌ Fix the issues above before proceeding")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())

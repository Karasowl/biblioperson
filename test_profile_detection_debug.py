import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from dataset.processing.profile_manager import ProfileManager
from dataset.processing.profile_detector import ProfileDetector, detect_profile_for_file, get_profile_detection_config

def test_profile_detection_pipeline():
    """Test profile detection at different stages of the pipeline"""
    
    file_path = r"C:\Users\adven\Downloads\Dario, Ruben - Antologia.pdf"
    
    print("=" * 80)
    print("🔍 DEBUGGING PROFILE DETECTION PIPELINE")
    print("=" * 80)
    
    # Extract content sample once for all tests
    content_sample = ""
    try:
        import fitz  # pymupdf
        
        doc = fitz.open(file_path)
        markdown_content = ""
        
        # Extract first few pages
        max_pages = min(5, len(doc))
        
        for page_num in range(max_pages):
            page = doc.load_page(page_num)
            page_markdown = page.get_text("markdown")
            
            if page_markdown.strip():
                markdown_content += page_markdown + "\n\n"
        
        doc.close()
        content_sample = markdown_content.strip()
        
        print(f"📄 Content sample extracted: {len(content_sample)} characters")
        
    except Exception as e:
        print(f"⚠️ Error extracting content sample: {e}")
        content_sample = ""
    
    # Test 1: Direct ProfileDetector
    print("\n📋 Test 1: Direct ProfileDetector")
    print("-" * 40)
    
    try:
        config = get_profile_detection_config()
        config['debug'] = True
        detector = ProfileDetector(config)
        
        result = detector.detect_profile(file_path)
        print(f"✅ ProfileDetector result: {result.profile_name} (confidence: {result.confidence:.3f})")
        
        for reason in result.reasons:
            print(f"   📋 {reason}")
            
    except Exception as e:
        print(f"❌ ProfileDetector error: {e}")
    
    # Test 2: detect_profile_for_file function
    print("\n📋 Test 2: detect_profile_for_file function")
    print("-" * 40)
    
    try:
        config = get_profile_detection_config()
        config['debug'] = True
        
        candidate = detect_profile_for_file(file_path, config)
        print(f"✅ detect_profile_for_file result: {candidate.profile_name} (confidence: {candidate.confidence:.3f})")
        
        for reason in candidate.reasons:
            print(f"   📋 {reason}")
            
    except Exception as e:
        print(f"❌ detect_profile_for_file error: {e}")
    
    # Test 3: ProfileManager.auto_detect_profile
    print("\n📋 Test 3: ProfileManager.auto_detect_profile")
    print("-" * 40)
    
    try:
        manager = ProfileManager()
        
        detected_profile = manager.auto_detect_profile(file_path, content_sample)
        print(f"✅ ProfileManager.auto_detect_profile result: {detected_profile}")
        
    except Exception as e:
        print(f"❌ ProfileManager.auto_detect_profile error: {e}")
    
    # Test 4: ProfileManager.get_profile_for_file (full method)
    print("\n📋 Test 4: ProfileManager.get_profile_for_file")
    print("-" * 40)
    
    try:
        manager = ProfileManager()
        
        suggested_profile = manager.get_profile_for_file(file_path, content_sample)
        print(f"✅ ProfileManager.get_profile_for_file result: {suggested_profile}")
        
    except Exception as e:
        print(f"❌ ProfileManager.get_profile_for_file error: {e}")
    
    # Test 5: Manual fallback method
    print("\n📋 Test 5: Manual fallback method")
    print("-" * 40)
    
    try:
        manager = ProfileManager()
        
        fallback_profile = manager._get_manual_profile_fallback(file_path)
        print(f"✅ Manual fallback result: {fallback_profile}")
        
    except Exception as e:
        print(f"❌ Manual fallback error: {e}")
    
    # Test 6: Check confidence threshold
    print("\n📋 Test 6: Confidence threshold analysis")
    print("-" * 40)
    
    try:
        config = get_profile_detection_config()
        config['debug'] = True
        
        candidate = detect_profile_for_file(file_path, config, content_sample)
        
        print(f"Detected profile: {candidate.profile_name}")
        print(f"Confidence: {candidate.confidence:.3f}")
        print(f"Threshold in auto_detect_profile: 0.35")
        print(f"Passes threshold: {candidate.confidence >= 0.35}")
        
        if candidate.confidence < 0.35:
            print("❌ ISSUE: Confidence below threshold, will fallback to manual method")
            print("   Manual method defaults to 'prosa' for PDF files")
        else:
            print("✅ Confidence above threshold, should use detected profile")
            
    except Exception as e:
        print(f"❌ Confidence analysis error: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 SUMMARY")
    print("=" * 80)
    print("This test shows exactly where the profile detection is failing")
    print("and why the full pipeline is using 'prosa' instead of 'verso'")

if __name__ == "__main__":
    test_profile_detection_pipeline() 
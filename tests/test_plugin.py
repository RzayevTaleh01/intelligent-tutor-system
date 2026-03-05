import pytest
from src.plugins.english.plugin import EnglishPlugin
from src.plugins.english.models import ItemType, LearningItem

@pytest.fixture
def plugin():
    return EnglishPlugin()

def test_get_content(plugin):
    # Test A2 level (mapped from 'easy')
    content = plugin.get_content("easy")
    assert content.content_id == "lesson_001"
    assert content.metadata["level"] == "A2"
    
    # Test B1 level (mapped from 'medium')
    content = plugin.get_content("medium")
    assert content.content_id == "lesson_002"
    assert content.metadata["level"] == "B1"

def test_generate_items_rule_based(plugin):
    # Setup context with lesson_001
    context = {"content_id": "lesson_001"}
    items_dicts = plugin.generate_items(context)
    
    assert len(items_dicts) > 0
    
    # Check item structure
    first_item = items_dicts[0]
    assert "id" in first_item
    assert "type" in first_item
    assert "prompt" in first_item
    assert "difficulty" in first_item

def test_grader_vocab_fill(plugin):
    # Create a mock item
    item = LearningItem(
        id="test_vocab",
        type=ItemType.VOCAB_FILL,
        prompt="Test prompt",
        expected_answer="apple",
        difficulty=2.0,
        skill_tag="vocab"
    )
    plugin.active_items[item.id] = item
    
    # Correct attempt
    result = plugin.grade_attempt(item.id, "apple")
    assert result.score == 1.0
    assert "Good job" in result.feedback_short
    
    # Incorrect attempt
    result = plugin.grade_attempt(item.id, "banana")
    assert result.score == 0.0
    assert "Not quite" in result.feedback_short

def test_grader_mcq(plugin):
    item = LearningItem(
        id="test_mcq",
        type=ItemType.GRAMMAR_MCQ,
        prompt="Test prompt",
        expected_answer="went",
        choices=["go", "went"],
        difficulty=2.0,
        skill_tag="grammar"
    )
    plugin.active_items[item.id] = item
    
    # Correct
    result = plugin.grade_attempt(item.id, "went")
    assert result.score == 1.0
    
    # Incorrect
    result = plugin.grade_attempt(item.id, "go")
    assert result.score == 0.0

def test_grader_rewrite_length_heuristic(plugin):
    item = LearningItem(
        id="test_rewrite",
        type=ItemType.REWRITE_SENTENCE,
        prompt="Rewrite this.",
        difficulty=3.0,
        skill_tag="writing"
    )
    plugin.active_items[item.id] = item
    
    # Too short
    result = plugin.grade_attempt(item.id, "Hi")
    assert result.score < 0.5
    assert "Too short" in result.errors
    
    # Decent length (mock logic assumes good score)
    result = plugin.grade_attempt(item.id, "This is a longer sentence for testing.")
    assert result.score > 0.5

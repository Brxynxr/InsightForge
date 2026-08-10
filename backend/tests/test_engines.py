from app.engines.base import EngineContext
from app.engines.context_models import EngineError, RecordDict
from app.engines.input.engine import InputEngine
from app.engines.tokenizer.engine import TokenizerEngine
from app.engines.validation.engine import ValidationEngine


def test_engine_context_default():
    ctx = EngineContext()
    assert ctx.batch_id == ""
    assert ctx.records == []
    assert ctx.errors == []
    assert ctx.results == []


def test_input_engine_missing_path():
    engine = InputEngine()
    ctx = EngineContext()
    result = engine.execute(ctx)
    assert len(result.errors) == 1
    assert result.errors[0].engine == "input"


def test_validation_engine_empty_records():
    engine = ValidationEngine()
    ctx = EngineContext(records=[], metadata={"required_columns": ["text"]})
    result = engine.execute(ctx)
    assert result.metrics.validated_count == 0


def test_validation_engine_missing_columns():
    engine = ValidationEngine()
    ctx = EngineContext(
        records=[RecordDict(other="value")],
        metadata={"required_columns": ["text"]}
    )
    result = engine.execute(ctx)
    assert result.metrics.validated_count == 0
    assert result.metrics.rejected_count == 1
    assert len(result.errors) == 1


def test_validation_engine_valid_record():
    engine = ValidationEngine()
    ctx = EngineContext(
        records=[RecordDict(text="hello", other="value")],
        metadata={"required_columns": ["text"]}
    )
    result = engine.execute(ctx)
    assert result.metrics.validated_count == 1
    assert result.metrics.rejected_count == 0
    assert len(result.records) == 1


def test_tokenizer_engine():
    engine = TokenizerEngine()
    ctx = EngineContext(records=[RecordDict(text="hello world")])
    result = engine.execute(ctx)
    assert result.metrics.total_tokens > 0
    assert len(result.records) == 1
    assert result.records[0].token_count is not None

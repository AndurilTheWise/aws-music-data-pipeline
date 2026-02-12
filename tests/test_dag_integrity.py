from airflow.models import DagBag


def _dagbag() -> DagBag:
    return DagBag(
        dag_folder="data_quality_and_orchestration/dags",
        include_examples=False,
    )


def test_dag_import_errors():
    dagbag = _dagbag()
    assert len(dagbag.import_errors) == 0, f"DAG import errors: {dagbag.import_errors}"


def test_expected_dags_exist():
    dagbag = _dagbag()
    assert dagbag.get_dag("deftunes_songs_pipeline_dag") is not None
    assert dagbag.get_dag("deftunes_api_pipeline_dag") is not None

import asyncio

from tmis.runtime_platform.load_testing.engine import LoadTestingEngine
from tmis.runtime_platform.load_testing.schemas import LoadTestPreset


def test_run_small_preset_reports_all_requests_successful() -> None:
    async def scenario() -> None:
        async def target() -> None:
            await asyncio.sleep(0)

        report = await LoadTestingEngine().run(LoadTestPreset.SMALL, target)

        assert report.concurrent_users == 100
        assert report.total_requests == 100
        assert report.success_count == 100
        assert report.error_count == 0
        assert report.throughput_rps > 0

    asyncio.run(scenario())


def test_run_records_errors_without_aborting_the_batch() -> None:
    async def scenario() -> None:
        async def flaky() -> None:
            raise RuntimeError("simulated failure")

        report = await LoadTestingEngine().run(10, flaky)

        assert report.total_requests == 10
        assert report.error_count == 10
        assert report.success_count == 0

    asyncio.run(scenario())


def test_requests_per_user_multiplies_total_requests() -> None:
    async def scenario() -> None:
        async def target() -> None:
            return None

        report = await LoadTestingEngine().run(5, target, requests_per_user=3)
        assert report.total_requests == 15

    asyncio.run(scenario())

from typing import Any, Dict, Optional

from airflow.models import BaseOperator
from airflow.utils.context import Context
from airflow.utils.decorators import apply_defaults

from airflow_provider_hex.hooks.hex import HexHook


class HexRunProjectOperator(BaseOperator):
    """Runs a Hex Project, and optionally waits until completion.

    :param project_id: Hex Project ID
    :type project_id: str
    :param hex_conn_id: connection run the operator with
    :type hex_conn_id: str
    :param synchronous: if true, wait for the project run to complete otherwise request
        a run but do not wait for completion. Useful for long-running projects that
        block the DAG from completing.
    :type synchronous: bool
    :param wait_seconds: interval to wait, in seconds, between successive API polls.
    :type wait_seconds: int
    :param timeout: maximum time to wait for a sync to complete before aborting the run.
        if kill_on_timeout is true, also attempt to end the project run
    :type timeout: int
    :param kill_on_timeout: if true attempt to stop the project if the timeout is
    reached. If false, the project will continue running indefinitely in the background
    until completion.
    :type kill_on_timeout: bool
    :param input_paramters: additional input parameters, a json-serializable dictionary
        of variable_name: value pairs.
    :type input_parameters: dict
    """

    template_fields = ["project_id"]
    ui_color = "#F5C0C0"

    @apply_defaults
    def __init__(
        self,
        project_id: str,
        hex_conn_id: str = "hex_default",
        synchronous: bool = True,
        wait_seconds: int = 3,
        timeout: int = 3600,
        kill_on_timeout: bool = True,
        input_parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.hex_conn_id = hex_conn_id
        self.synchronous = synchronous
        self.wait_seconds = wait_seconds
        self.timeout = timeout
        self.kill_on_timeout = kill_on_timeout
        self.input_parameters = input_parameters

    def execute(self, context: Context) -> Any:
        hook = HexHook(self.hex_conn_id)

        if self.synchronous:
            self.log.info("Starting Hex Project")
            resp = hook.run_and_poll(
                self.project_id,
                inputs=self.input_parameters,
                poll_interval=self.wait_seconds,
                poll_timeout=self.timeout,
                kill_on_timeout=self.kill_on_timeout,
            )
            self.log.info("Hex Project completed successfully")

        else:
            self.log.info("Starting Hex Project asynchronously")
            resp = hook.run_project(self.project_id, inputs=self.input_parameters)
            self.log.info("Hex Project started successfully.")

        try:
            self.log.info(dict(resp))
            return resp
        except TypeError:
            self.log.warning("Failed to parse response from API %s", resp)
            return resp

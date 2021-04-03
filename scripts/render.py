#!/usr/bin/env python
#
# Requires:
# conda create -n prefect -c conda-forge prefect
#

from prefect import Flow, Parameter, task, unmapped
from prefect.executors import LocalDaskExecutor
from prefect.tasks.shell import ShellTask
from prefect.utilities.debug import raise_on_exception
from omero.cli import cli_login
from omero.gateway import BlitzGateway

name = Parameter("name")


shell = ShellTask(
    return_all=True,
    log_stderr=True)


COMMAND = "/opt/omero/server/OMERO.server/bin/omero"

@task
def render(object, name):
    return (
        f"{COMMAND} render set {object} "
        f"/uod/idr/metadata/idr0072-schormann-subcellref/"
        f"{name}/idr0072-{name}-render.yml")


@task
def list_children(name, ignore):
    with cli_login() as cli:
        conn = BlitzGateway(client_obj=cli.get_client())
        screen = conn.getObject('Screen', attributes={
            'name': "idr0072-schormann-subcellref/" + name})
        return [f"Plate:{x.id}" for x in screen.listChildren()]


with Flow("idr0093") as flow:
    key = shell(command=f"{COMMAND} login demo@localhost")
    children = list_children(name, key)
    render_commands = render.map(children, name=unmapped(name))
    rendered = shell.map(command=render_commands)


if __name__ == "__main__":
    with raise_on_exception():
        flow.executor = LocalDaskExecutor(scheduler="threads", num_workers=5)
        flow.run(name="screenA")
        flow.run(name="screenB")

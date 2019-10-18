from typing import Union, List, Optional
import logging
import click
import aws

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@click.group()
def cli():
    pass

@cli.command("delete", help='Delete one or several HITs')
@click.option('--all_hits',
              default=False,
              is_flag=True,
              help="Delete all HITs related to account")
@click.option('--hit_id',
              default=None,
              help="Specific HITId",
              multiple=True)
def delete(all_hits: bool = False,
           *hit_ids: Optional[List[str]]):
    client = aws.connect_mturk()

    if all_hits:
        aws.delete_all_hits(client)
    elif hit_ids is not None:
        for hit_id in hit_ids:
            aws.delete_hit(client, hit_id)
    else:
        aws.delete_recorded_hits(client)


@cli.command("progress", help='Show progress')
@click.option('--all_hits',
              default=False,
              is_flag=True,
              help="Show progress on all HITs related to account")
@click.option('--hit_ids',
              default=None,
              help="Specific HITId",
              multiple=True)
def progress(all_hits: bool = False,
             hit_ids: Optional[List[str]] = None):

    client = aws.connect_mturk()

    if all_hits:
        aws.progress_all_hits(client)
    elif hit_ids is not None:
        aws.progress_hits(client, hit_ids)
    else:
        aws.progress_recorded_hits(client)

if __name__ == "__main__":
    cli()

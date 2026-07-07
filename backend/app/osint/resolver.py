
from .entity import Person


def resolve(workers):

    person=Person()

    for worker in workers:

        if isinstance(worker,Exception):
            continue

        provider=worker.get("provider")

        if provider=="github":

            d=worker["data"]

            person.name=d.get("name") or person.name

            person.github=d.get("username") or person.github

            person.company=d.get("company") or person.company

            person.bio=d.get("bio") or person.bio

            person.location=d.get("location") or person.location

            person.website=d.get("blog") or person.website

            person.evidence.append(worker)

    return person

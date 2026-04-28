from prolog_api import PrologService


def main():
    api = PrologService("knowledge/context.pl")

    request = {
        "action": "people_with_skill",
        "params": {
            "skill": "python"
        }
    }

    response = api.handle_request(request)
    print(response)

    response = api.handle_request({
        "action": "project_members",
        "params": {
            "project": "alpha"
        }
    })
    print(response)

    response = api.handle_request({
        "action": "suitable_for_project",
        "params": {
            "person": "alice",
            "project": "alpha"
        }
    })
    print(response)

    response = api.handle_request({
        "action": "raw_query",
        "params": {
            "query": "role(Person, Role)"
        }
    })
    print(response)


if __name__ == "__main__":
    main()
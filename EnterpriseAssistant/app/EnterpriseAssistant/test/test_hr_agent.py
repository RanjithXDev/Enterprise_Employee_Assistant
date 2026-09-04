from agents.hr_agent import create_hr_agent


def main():
    hr_agent = create_hr_agent()

    print("HR Agent created successfully.")
    print()

    response = hr_agent(
    "Requester ID: EMP001\n"
    "Request: What is the company leave policy?"
    )

    print("HR Agent response:")
    print(response)


if __name__ == "__main__":
    main()
    
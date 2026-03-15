from pathlib import Path


def get_user_input():
    user_input = input("User: ").strip()

    if user_input.lower() == "exit":
        print("\nExiting the Application!! Thank you!!")
        return "exit"

    if not user_input:
        print("\nEnter a valid message\n")
        return None

    return user_input


def print_url_summaries(service):
    url_summaries = service.state.get("latest_url_summaries") or []
    if not url_summaries:
        return

    print("GPT: Here is the summary of the inspiration URL(s) I used:\n")
    for idx, item in enumerate(url_summaries, start=1):
        url = item.get("url", "Unknown URL")
        summary = item.get("summary", "No summary available.")
        print(f"GPT: [{idx}] URL: {url}")
        print(f"GPT: Summary: {summary}\n")


def chat(service):
    print("\n\n======================== Local ChatGPT Terminal App ========================\n")
    print("Type EXIT to stop the app.\n")

    while True:
        user_input = get_user_input()

        if user_input == "exit":
            break

        if user_input is None:
            continue

        outcome = service.handle_turn(user_input)

        if not outcome.ok:
            print(f"\nError: {outcome.response}\n")
            if outcome.should_exit:
                break
            continue

        response = outcome.response

        if service.is_html(response.message):
            output_path = service.state.get("current_html_path")

            print_url_summaries(service)

            print("\nGPT: Portfolio HTML generated and validated successfully.\n")

            if output_path:
                resolved = Path(output_path).resolve()
                exists_now = resolved.exists()
                print(f"GPT: I saved the latest version to: {resolved}\n")
                print(f"GPT: File exists: {'Yes' if exists_now else 'No'}\n")
                print("GPT: Please open this file in your browser, review it, and then respond.\n")
            else:
                print("GPT: Warning: HTML was generated, but no saved file path was found in state.\n")

            print("GPT: Send a rating from 1-10 after viewing it.\n")
            print("GPT: If your rating is 8, 9, or 10, I will keep this version and exit.\n")
            print("GPT: If your rating is 7 or below, I will ask what to improve and create a new saved version.\n")
        else:
            print(f"\nGPT: {response.message}\n")

        if outcome.should_exit:
            break
import sys
import argparse

def main():
    if len(sys.argv) > 1:
        subcommand = sys.argv[1]
        
        if subcommand == "--help" or subcommand == "-h":
            print("Usage: python -m term <command> [args...]")
            print("\nCommands:")
            print("  agent <goal>             Execute a goal directly (non-interactive)")
            print("  agent [user@host]        Launch the interactive agent locally or remotely")
            print("  chat                     Launch the chat interface")
            print("  prompt                   Launch the prompt creator")
            print("  api                      Start the API server")
            sys.exit(0)
            
        if subcommand == "agent":
            sys.argv = ["term_ag.py"] + sys.argv[2:]
            import term_ag
            if hasattr(term_ag, "main"):
                term_ag.main()
            return
        elif subcommand == "chat":
            sys.argv = ["term_ask.py"] + sys.argv[2:]
            import term_ask
            if hasattr(term_ask, "main"):
                term_ask.main()
            return
        elif subcommand == "prompt":
            sys.argv = ["PromptCreator.py"] + sys.argv[2:]
            import PromptCreator
            if hasattr(PromptCreator, "main"):
                PromptCreator.main()
            return
        elif subcommand == "api":
            sys.argv = ["term_api.py"] + sys.argv[2:]
            import term_api
            if hasattr(term_api, "main"):
                term_api.main()
            return

    print("Usage: python -m term <command> [args...]")
    print("\nCommands:")
    print("  agent <goal>             Execute a goal directly (non-interactive)")
    print("  agent [user@host]        Launch the interactive agent locally or remotely")
    print("  chat                     Launch the chat interface")
    print("  prompt                   Launch the prompt creator")
    print("  api                      Start the API server")
    sys.exit(1)

if __name__ == "__main__":
    main()
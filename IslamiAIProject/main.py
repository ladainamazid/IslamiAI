# File: main.py
# Main application

from query_parser import parse_user_query
from retrieval import retrieve_ruling
from formatter import format_answer

def main():
    print("\n" + "="*50)
    print("ISLAMIC AI - SIMPLE PROTOTYPE")
    print("Tanya tentang hukum kerja")
    print("Ketik 'exit' untuk keluar")
    print("="*50 + "\n")
    
    while True:
        # User input
        question = input("📝 Pertanyaan Anda: ")
        
        # Check exit
        if question.lower() == "exit":
            print("Terima kasih. Wassalam.")
            break
        
        # Parse
        topic = parse_user_query(question)
        
        # Retrieve
        result = retrieve_ruling(topic)
        
        # Format & display
        answer = format_answer(result)
        print(answer)
        print()

if __name__ == "__main__":
    main()

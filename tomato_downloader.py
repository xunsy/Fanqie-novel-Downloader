# -*- coding: utf-8 -*-

"""
Tomato Novel Downloader
"""

from api import TomatoAPI
import json

def main():
    api = TomatoAPI()
    search_cache = {}

    while True:
        print("\nTomato Novel Downloader")
        print("1. Search for a book")
        print("2. Download a book by ID")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            keyword = input("Enter keyword to search: ")
            search_results = api.search(keyword)
            if search_results and 'data' in search_results and 'search_tabs' in search_results['data'] and search_results['data']['search_tabs']:
                print("Search Results:")
                search_cache.clear()
                for book in search_results['data']['search_tabs']['data']:
                    if 'book_data' in book and book['book_data']:
                        book_id = book.get('book_id')
                        book_data_list = book['book_data']
                        if book_data_list:
                            book_data_dict = book_data_list
                            book_name = book_data_dict.get('book_name')
                            author = book_data_dict.get('author')
                            abstract = book_data_dict.get('abstract')
                            
                            if book_id and book_name:
                                search_cache[book_id] = {'book_name': book_name, 'author': author, 'abstract': abstract}
                                print(f"  ID: {book_id}, Title: {book_name}")
            else:
                print("No results found or an error occurred.")

        elif choice == '2':
            book_id = input("Enter book ID to download: ")
            if book_id in search_cache:
                book_data = search_cache[book_id]
                print("\nBook Information:")
                print(f"  Title: {book_data.get('book_name')}")
                print(f"  Author: {book_data.get('author')}")
                print(f"  Description: {book_data.get('abstract')}")

                book_info = api.get_book_info(book_id)
                
                if book_info and 'data' in book_info and 'chapterListWithVolume' in book_info['data'] and book_info['data']['chapterListWithVolume']:
                    item_ids = [item['itemId'] for item in book_info['data']['chapterListWithVolume']]
                    
                    print("\nDownloading chapters...")
                    full_content = ""
                    
                    item_id_chunks = [item_ids[i:i + 30] for i in range(0, len(item_ids), 30)]
                    
                    for chunk in item_id_chunks:
                        item_ids_str = ",".join(map(str, chunk))
                        content_data = api.get_content(item_ids=item_ids_str, api_type='batch')
                        if content_data and 'data' in content_data:
                            for chapter_content in content_data['data']:
                                full_content += f"\n\n## {chapter_content.get('title', '')}\n\n"
                                full_content += chapter_content.get('content', '')
                        else:
                            print(f"Could not download chapters chunk: {item_ids_str}")

                    file_name = f"{book_data.get('book_name', 'book')}.txt"
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write(full_content)
                    print(f"Book downloaded successfully as {file_name}")

                else:
                    print("Could not retrieve chapter list.")
            else:
                print("Book ID not found in search results. Please search for the book first.")

        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    main()
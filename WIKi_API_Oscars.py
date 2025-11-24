"""
    The intention of this script is to create a list of Oscar winning films which came after 1995 while their directors
    were born before 1955 using the Wikipedia API and Webscraping
"""


import wikipedia
from bs4 import BeautifulSoup
import re


def get_string_with_largest_number(data_list):
    """
    Finds the string in a list that contains the largest integer number.

    Args:
        data_list (list): A list of strings.

    Returns:
        str or None: The string containing the largest number, 
                     a specific message if no string contains a number,
                     or None if the input list is empty.
    """
    if not data_list:
        return None

    def extract_number(s):
        """
        Helper function to extract the first integer found in a string.
        Returns -1 if no sequence of digits is found.
        """
        match = re.search(r'\d+', s)

        if match:
            return int(match.group(0))
        else:
            return -1

    result_string = max(data_list, key=extract_number)

    if extract_number(result_string) == -1:
        return f"No string in the list contained a valid number (digits)."

    return result_string

def get_directors_name(movie_title, flag = True):
    """
    Scrapes a Wikipedia page for a movie to find the director's name(s).

    It handles page errors, disambiguation pages, and recursively retries 
    by appending '(film)' to the title if the 'Directed by' field is missing 
    on the initial page.

    Args:
        movie_title (str): The title of the movie to search on Wikipedia.
        flag (bool, optional): A flag used for recursive calls to prevent 
                               infinite loops when appending '(film)'. Defaults to True.

    Returns:
        str or list: The director's name (str) or a list of names (list), 
                     or an empty string/error message on failure.
    """

    # --- 1. Fetch Wikipedia Page and Handle Exceptions ---
    try:
        # Attempt to fetch the Wikipedia page content for the given movie_title.
        page = wikipedia.page(movie_title, auto_suggest=False)
        soup = BeautifulSoup(page.html(), 'html.parser')
    except wikipedia.exceptions.PageError:
        # Catch exception if the page is not found (e.g., bad title).
        print(f"PageError: Wikipedia page for '{movie_title}' not found")
        return ""
    except wikipedia.exceptions.DisambiguationError as d:
        # Filter the options suggested by Wikipedia to only include titles that contain the word "film".
        # If filtering results in exactly one title, assume it's the correct one and recursively call the function with the new title.
        filtered_titles = [title for title in d.options if "film" in title]
        if len(filtered_titles) == 1:
            return get_directors_name(filtered_titles[0],year)
        # If there are multiple 'film' titles, try to pick the most likely one using an external function choosing the latest title
        filtered_titles = get_string_with_largest_number(filtered_titles)
        return get_directors_name(filtered_titles)

    except Exception as e:
        print(f"An error occurred: {e}")
        return ""
        
    # --- 2. Locate Infobox Table ---
    # Find the main information table (infobox) on the Wikipedia page
    infobox = soup.find('table', class_='infobox')

    if not infobox:
        return f"Director: Infobox table not found on the page for '{movie_title}'."

    # --- 3. Locate 'Directed by' Header ---
    # Search within the infobox for a table header ('th') whose exact
    director_header = infobox.find('th', string='Directed by')

    # --- 4. Extract Director Data ---
    if director_header:
        director_data_cell = director_header.find_next_sibling('td', class_='infobox-data')

        if director_data_cell:
            director_link = director_data_cell.find_all('a')
            if director_link:
                if len(director_link) == 1:
                    director_link = director_link[0]
                    return director_link.text
                if len(director_link) > 1:
                    return [element.text for element in director_link]
                else:
                    return director_data_cell.text.strip()
        else:
            print(f"Director: Data cell for 'Directed by' not found.")
            return ""
            
    # --- 5. Handle Missing Header ---
    else:
        if flag:
            new_title = f"{movie_title} (film)"
            return get_directors_name(new_title, year, flag = False)
        print(f"Director: Header 'Directed by' not found in the Infobox.")
        return ""


def get_directors_BY(director):
    """
    Scrapes a Wikipedia page for a director's birth year.
    It attempts to find the year using standard date formatting, text after 
    a line break, or the start of the data cell content.

    Args:
        director (str): The name of the person (director) to search on Wikipedia.

    Returns:
        str: The four-digit birth year (as a string), or an empty string "" 
             on failure or error.
    """
    # --- 1. Fetch Wikipedia Page and Handle Exceptions ---
    try:
        # Attempt to fetch the Wikipedia page content for the given director name
        page = wikipedia.page(director, auto_suggest=False)
        soup = BeautifulSoup(page.html(), 'html.parser')
    # Handle case where the Wikipedia page for the name is not found.
    except wikipedia.exceptions.PageError:
        print(f"Error: Wikipedia page for '{director}' not found.")
        return ""
    # Handle any other unexpected exceptions during page fetching/parsing.
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""
        
    # --- 2. Locate Infobox Table ---
    # Find the main information table (infobox) on the Wikipedia page
    infobox = soup.find('table', class_='infobox')

    if not infobox:
        print(f"Director: Infobox table not found on the page for '{director}'")
        return ""
    # --- 3. Extract Birth Year using Different Methods ---
    try:
        director_header = infobox.find('th', string='Born')
        director_data_cell = director_header.find_next_sibling('td', class_='infobox-data')
        # Method 1: Look for the standard 'bday' class (ISO 8601 date format)
        bday_span = director_data_cell.find('span', class_='bday')
        if bday_span:
            full_date = bday_span.text.strip()
            if full_date and len(full_date) >= 4:
                return full_date[:4]
        # Method 2: Look for text content immediately following a line break (<br>)
        if director_data_cell.find('br'):
            br_tag = director_data_cell.find('br')
            raw_text = br_tag.next_sibling
            if isinstance(raw_text, str):
                if re.search(r'\d', raw_text):
                    return br_tag.next_sibling[0:4]
        # Method 3: Look at the very start of the data cell's content
        if director_data_cell.contents:
            if director_data_cell.contents[0].strip()[0:4].isnumeric() :
                    return director_data_cell.contents[0].strip()[0:4]
    # Handles errors like trying to access methods on None if an element wasn't found
    except TypeError as e:
        print(f"Error: 'NoneType' object is not callable")
        return ""
    except AttributeError as e:
        print(f"Error: 'NoneType' object has no attribute 'find_next_sibling")
        return ""
    except:
        print(f"undiagnosed error")
        return ""
        
    # If none of the extraction methods succeed, return an empty string.
    return ""

def get_names_and_years():
    """
    Scrapes the Wikipedia list of Academy Award-winning films, extracts film
    details (name, year), finds the director(s), and then determines the 
    director's birth year. It filters the results to only include films
    winning an oscar after 1995 directed by individuals born before 1955 .

    Returns:
        list: A list of dictionaries, where each dictionary contains 
              details for a film that meets the criterion.
    """

    # Dictionary mapping ambiguous film titles to their specific Wikipedia page titles to handle disambiguation issues without complex logic.
    problematic_films = {"Conclave":"Conclave (film)","War Is Over! Inspired by the Music of John and Yoko":"War Is Over!",
                         "Dune":"Dune (2021 film)", "King Richard":"King Richard (film)",
                         "Soul":"Soul (2020 film)", "Moonlight":"Moonlight (2016 film)"}

    # Cache to store directors' birth years to avoid making redundant network calls for directors who have worked on multiple Oscar-winning films.
    known_directors = {}
    title = "List of Academy Award–winning films"
    # --- 1. Fetch and Parse Wikipedia Page ---
    page = wikipedia.page(title, auto_suggest=False)

    soup = BeautifulSoup(page.html(), 'html.parser')
    
    # --- 2. Locate the Target Table ---
    # Find all tables with the classes 'wikitable' and 'sortable'.
    movies = soup.find_all('table', class_='wikitable sortable')
    target_table = movies[0]
    rows = target_table.find('tbody').find_all('tr')
    # List to store the final filtered film data.
    film_list = []

    # --- 3. Iterate Through Table Rows ---
    # Skip the header row (index 0), iterate over film data rows (rows[1:]).
    for row in rows[1:]:
        # Get all data cells ('td') in the current row.
        cells = row.find_all('td')

        # Check if the row has enough cells (at least 2 for Film Name and Year)
        if len(cells) >= 2:
            # Extract Film Name from the first cell (cells[0]).
            film_element = cells[0].find('a')
            film_name = film_element.text.strip() if film_element else "N/A"
            # Apply corrections for films with known title ambiguities.
            if film_name in problematic_films:
                film_name = problematic_films[film_name]
                
            # Extract Year from the second cell (cells[1]).
            year_text = cells[1].text.strip()

            # Stop condition: Terminate the search when the year 1995 is reached.
            if len(year_text) == 4:
                if int(year_text) == 1995:
                    break
            # Handle cases where the year text contains extraneous characters
            if len(year_text) > 4:
                year_text=year_text[0:4]

            # --- 4. Get Director Name(s) ---
            # Call the external helper function to find the director.
            director = get_directors_name(film_name)
            # --- 5. Process Single Director Case (director is a string) ---
            if isinstance(director,str):
                # Check the cache before scraping the director's page.
                if director in known_directors:
                    director_BY = known_directors[director]
                else:
                    director_BY = get_directors_BY(director)
                    known_directors[director] = director_BY
                    
                # Filtering: Check if the director's birth year was found and meets the criterion.
                if director_BY == "":
                    continue
                if int(director_BY) >= 1955:
                    continue


                film_list.append({
                    "Film Name": film_name,
                    "Year": year_text,
                    "Director Name": director,
                    "Director Birth year":director_BY
                })
                print(f"extracted Film: {film_name}, Year: {year_text}, Director Name: {director}, Director Birth year: {director_BY}")
            else:
                # --- 6. Process Multiple Directors Case (director is a list) ---
                director_list = director
                director = None

                if director_list is None:
                    continue
                else:
                    # Iterate through each director in the list.
                    for director in director_list:
                        if director in known_directors:
                            director_BY = known_directors[director]
                        else:
                            director_BY = get_directors_BY(director)
                            known_directors[director] = director_BY

                        if director_BY == "":
                            continue
                        if int(director_BY) >= 1955:
                            continue
                        # Add the film's data (paired with the current director) to the result list.
                        film_list.append({
                            "Film Name": film_name,
                            "Year": year_text,
                            "Director Name": director,
                            "Director Birth year": director_BY
                        })
                        print(
                            f"extracted Film: {film_name}, Year: {year_text}, Director Name: {director}, Director Birth year: {director_BY}")
    # --- 7. Return Final Results ---
    return film_list


complete_list = get_names_and_years()

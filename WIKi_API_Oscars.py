import wikipedia
from bs4 import BeautifulSoup
import re


def get_string_with_largest_number(data_list):
    if not data_list:
        return None

    def extract_number(s):
        match = re.search(r'\d+', s)

        if match:
            return int(match.group(0))
        else:
            return -1

    result_string = max(data_list, key=extract_number)

    if extract_number(result_string) == -1:
        return f"No string in the list contained a valid number (digits)."

    return result_string

def get_directors_name(movie_title, year, flag = True):

    try:
        page = wikipedia.page(movie_title, auto_suggest=False)
        soup = BeautifulSoup(page.html(), 'html.parser')
    except wikipedia.exceptions.PageError:
        print(f"PageError: Wikipedia page for '{movie_title}' not found")
        return ""
    except wikipedia.exceptions.DisambiguationError as d:
        filtered_titles = [title for title in d.options if "film" in title]
        if len(filtered_titles) == 1:
            return get_directors_name(filtered_titles[0],year)
        filtered_titles = get_string_with_largest_number(filtered_titles)
        return get_directors_name(filtered_titles, year)

    except Exception as e:
        print(f"An error occurred: {e}")
        return ""

    # 1. Target the main Infobox table
    infobox = soup.find('table', class_='infobox')

    if not infobox:
        return f"Director: Infobox table not found on the page for '{movie_title}'."

    director_header = infobox.find('th', string='Directed by')

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
    else:
        if flag:
            new_title = f"{movie_title} (film)"
            return get_directors_name(new_title, year, flag = False)
        print(f"Director: Header 'Directed by' not found in the Infobox.")
        return ""


def get_directors_BY(director):
    try:
        page = wikipedia.page(director, auto_suggest=False)
        soup = BeautifulSoup(page.html(), 'html.parser')
    except wikipedia.exceptions.PageError:
        print(f"Error: Wikipedia page for '{director}' not found.")
        return ""
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""

    infobox = soup.find('table', class_='infobox')

    if not infobox:
        print(f"Director: Infobox table not found on the page for '{director}'")
        return ""
    try:
        director_header = infobox.find('th', string='Born')
        director_data_cell = director_header.find_next_sibling('td', class_='infobox-data')
        bday_span = director_data_cell.find('span', class_='bday')
        if bday_span:
            full_date = bday_span.text.strip()
            if full_date and len(full_date) >= 4:
                return full_date[:4]

        if director_data_cell.find('br'):
            br_tag = director_data_cell.find('br')
            raw_text = br_tag.next_sibling
            if isinstance(raw_text, str):
                if re.search(r'\d', raw_text):
                    return br_tag.next_sibling[0:4]

        if director_data_cell.contents:
            if director_data_cell.contents[0].strip()[0:4].isnumeric() :
                    return director_data_cell.contents[0].strip()[0:4]

    except TypeError as e:
        print(f"Error: 'NoneType' object is not callable")
        return ""
    except AttributeError as e:
        print(f"Error: 'NoneType' object has no attribute 'find_next_sibling")
        return ""
    except:
        print(f"undiagnosed error")
        return ""

def get_names_and_years():
    problematic_films = {"Conclave":"Conclave (film)","War Is Over! Inspired by the Music of John and Yoko":"War Is Over!",
                         "Dune":"Dune (2021 film)", "King Richard":"King Richard (film)",
                         "Soul":"Soul (2020 film)", "Moonlight":"Moonlight (2016 film)"}
    known_directors = {}
    title = "List of Academy Award–winning films"
    page = wikipedia.page(title, auto_suggest=False)

    soup = BeautifulSoup(page.html(), 'html.parser')

    movies = soup.find_all('table', class_='wikitable sortable')
    target_table = movies[0]
    rows = target_table.find('tbody').find_all('tr')
    film_list = []

    for row in rows[1:]:
        cells = row.find_all('td')

        if len(cells) >= 2:
            film_element = cells[0].find('a')
            film_name = film_element.text.strip() if film_element else "N/A"
            if film_name in problematic_films:
                film_name = problematic_films[film_name]

            year_text = cells[1].text.strip()

            if len(year_text) == 4:
                if int(year_text) == 1995:
                    break
            if len(year_text) > 4:
                year_text=year_text[0:4]

            director = get_directors_name(film_name,year_text)
            if isinstance(director,str):

                if director in known_directors:
                    director_BY = known_directors[director]
                else:
                    director_BY = get_directors_BY(director)
                    known_directors[director] = director_BY

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
                director_list = director
                director = None

                if director_list is None:
                    continue
                else:
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

                        film_list.append({
                            "Film Name": film_name,
                            "Year": year_text,
                            "Director Name": director,
                            "Director Birth year": director_BY
                        })
                        print(
                            f"extracted Film: {film_name}, Year: {year_text}, Director Name: {director}, Director Birth year: {director_BY}")

    return film_list


complete_list = get_names_and_years()
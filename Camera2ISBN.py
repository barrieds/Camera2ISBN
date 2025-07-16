import easyocr
import cv2
import requests
import json
import time
from itertools import combinations

def RequestFun(texts):
    #Empty list to store returned image in a format suitable for the API
    queries = []

    #This is what adds the queries to the list in the suitable format
    #It works by extending the list with a bunch of combinations joined together by a space (joined together in 2s and 3s)
    for size in [2,3]:
        queries.extend([' '.join(combo) for combo in combinations(texts, size)])

    #Dictionary to store possible book data returned from the API
    PossibleBooks = {}
    #This set is used to make sure there are no copies of the same book data
    Identifiers = set()

    print("Showing Possible Books")

    count = 1

    #For loop to request the data using all of the combinations of queries
    for query in queries:
        r = requests.get(f'https://openlibrary.org/search.json?q={query}')
        #data is what holds the json data returned from the API
        data = r.json()

        #This gets the data found in the json data based on whether or not the number of books found is equal to or above one
        if data["numFound"] >= 1:
            title = data["docs"][0].get("title", "Unknown Title")
            author = data["docs"][0].get("author_name", ["Unknown Author"])[0]
            ISBN = data["docs"][0].get("ia", ["Unknown ISBN"])[0]

            #This checks for copies and skips it if it is
            if ISBN in Identifiers:
                continue

            print(f"\nBook: {title} by {author}")

            #This checks to see if the returned identifier was an ISBN or something different
            if ISBN[:5] != "isbn_":
                print(f"Internet Archive Identifier: {ISBN}")
            else:
                print(f"ISBN: {ISBN}")
            
            print(f"Link: {r.url}")

            #This adds the identifier so that the next loop knows what has already been requested
            Identifiers.add(ISBN)
            #This adds the returned data to the dictonary
            PossibleBooks[title] = (author, ISBN)

            count = count + 1

            #This is used to leave breathing room for the API requests
            time.sleep(0.5)

            if count == 6:
                break

    #This prints out the book titles received in a list format
    print("\nPossible Book List:\n")
    for title in PossibleBooks:
        print(f"Title: {title}")
    
    #This section lets the user make sure out of the options that their books is there
    print("\nIf your book is in the returned list type out its title")
    book = input("Book: ")

    if book in PossibleBooks:
        author, ISBN = PossibleBooks[book]
        print(f"\nThe book is {book} by {author}")
        print(f"ISBN: {ISBN[5:]}")
    else:
        print("Book was not included in returned list")
        nobook = 1
        return nobook


#Opens the camera
camera = cv2.VideoCapture(0)

ret, frame = camera.read()

#this checks to make sure that the camera is working
if ret:
    cv2.imshow("Captured", frame)
    cv2.imwrite("bookimage.png", frame)
    cv2.waitKey(0)
    cv2.destroyWindow("Captured")
else:
    print("Failed to capture image")

#Closes the camera
camera.release()

#Test image, the actual input will be from the users camera
bookimage = 'bookimage.png'

#This loads the image for OpenCV
loaded_img = cv2.imread(bookimage)

#imagechange = cv2.bilateralFilter(loaded_img, 11, 17, 17)
#imagechange = cv2.convertScaleAbs(imagechange, alpha=0.5, beta=-0.5)

#These are the filters placed on the image to make text more readable
imagechange = cv2.cvtColor(loaded_img, cv2.COLOR_BGR2GRAY)
imagechange = cv2.bilateralFilter(imagechange, 11, 17, 17)
imagechange = cv2.equalizeHist(imagechange)
imagechange = cv2.adaptiveThreshold(imagechange, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
imagechange = cv2.resize(imagechange, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

#This creates an image with the filters to see how the filters changed the image
bookdebug = cv2.imwrite("bookdebug.png", imagechange)

#This loads the OCR model
reader = easyocr.Reader(['en'], gpu=False)

#This is what reads the text from the image
result = reader.readtext(imagechange)

#The _'s is telling the return values to ignore that value, the values are bbox, text, confidence
texts = [text for _, text, _ in result]

for text in texts:
    print(text)

#This part uses the function to instead use text in case the book could not be found using the camera
while True:
    result = RequestFun(texts)
    if result != 1:
        break
    print("\nInput book via text")
    bookinput = input("Book: ")
    texts = bookinput.split()


#In the future, code will be added to add missing books or misfindings so that more accurate results are obtained
import random, os
from sys import platform


letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

stages = ['''
  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|\  |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
  |   |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
      |
      |
      |
=========
''', '''
  +---+
  |   |
      |
      |
      |
      |
=========
''']

word_list = ["aardvark", "baboon", "camel", "onion", "desktop", "farting", "elephant", "trailer", "thermos", "potato", "smartphone", "chatroom", "aisle", "transmission", "racecar", "giraffe", "airplane", "bonfire", "business", "contrast", "disaster", "endeavor", "exchange", "invasion"]
word = word_list[random.randint(0, len(word_list)-1)]
# print("THE WORD IS ", word)
display = []
end_of_game = False
lives = 6
old_guesses = []

for letter in word:
  display.append("_")

while not end_of_game:

  guess = input("Enter guess: ")
  while (guess not in letters) or (guess in old_guesses):
    print("Invalid or already guessed! Try again: ")
    guess = input("Enter guess: ")
  old_guesses.append(guess)

  if "linux" in platform:
    os.system("clear")
  elif "win" or "nt" in platform:
    os.system("cls")
  
  for i in range(len(word)):
      if guess.lower() == word[i]:
        display[i] = guess.lower()

  if guess not in word:
        lives -= 1
        if lives == 0:
            end_of_game = True
            print("---------\nYOU LOSE!\n---------")
          
  if "_" not in display:    
    end_of_game = True
    print("---------\nYOU WIN!!\n---------")


  
  print(f"{' '.join(display)}")
  print(stages[lives])

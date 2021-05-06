# -*- coding: utf-8 -*-
"""GalaxyClassification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zoOBrFwpUk3c3icEZ1cszLzlRNe7uOwd
"""

import pandas as pd
import numpy as np
import os

# image manipulation libraries
from skimage.io import imread
from skimage.transform import resize
from PIL import Image
from keras.preprocessing.image import img_to_array

# machine learning libraries
from sklearn.model_selection import train_test_split
import keras
from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D, PReLU
from keras.models import load_model

# model and image visualization libraries
import matplotlib.pyplot as plt

# preload path names for ease of use
path = "drive/MyDrive/GalaxyClassification"
image_path = "drive/MyDrive/GalaxyClassification/training_images"
processed_data_path = "drive/MyDrive/GalaxyClassification/processed_data.csv"

solutions = pd.read_csv("drive/MyDrive/GalaxyClassification/training_solutions_rev1.csv")
solutions

"""The Classes with the same A value (format Class A.B) sum to 1, each B value is the percent of users that identified the galaxy as having the identified feature.

* Class 1.1: smooth and rounded
* Class 1.2: features or disk
* Class 1.3: star or artifact
* 
* Class 2.1: disk viewed edge-on
* Class 2.2: no
* 
* Class 3.1: bar feature
* Class 3.2: no
*
* Class 4.1: spiral arms
* Class 4.2: no
*
* Class 5.1: no bulge
* Class 5.2: just noticeable bulge
* Class 5.3: obvious bulge
* Class 5.4: dominant bulge
*
* Class 6.1: something odd (possible feature)
* Class 6.2: no
* 
* Class 7.1: completely round
* Class 7.2: in between
* Class 7.3: cigar shaped
*
* Class 8.1: ring
* Class 8.2: lens or arc
* Class 8.3: disturbed
* Class 8.4: irregular
* Class 8.5: other
* Class 8.6: merger
* Class 8.7: dust lane
* 
* Class 9.1: rounded bulge
* Class 9.2: boxy bulge
* Class 9.3: no bulge
*
* Class 10.1: tightly wound spiral arms
* Class 10.2: medium windedness
* Class 10.3: loosely wound spiral arms
*
* Class 11.1: 1 arm
* Class 11.2: 2 arms
* Class 11.3: 3 arms
* Class 11.4: 4 arms
* Class 11.5: 5+ arms
* Class 11.6: Can't tell arm number

# Test Image Data and Methods
"""

# find amount to crop galaxies to get the main image to classify
galaxy = Image.open("drive/MyDrive/GalaxyClassification/training_images/102433.jpg")
galaxy

# resized to allow for easier cropping increments
galaxy_cropped = galaxy.resize((500,500)).crop((175,175,325,325))
galaxy_cropped

galaxy_cropped.size # check size to potentially resize later

# now able to easily crop galaxies en mass
def crop_galaxy(image):
  return image.resize((500,500)).crop((175,175,325,325))

# check another random galaxy to ensure that cropping is generalizable
crop_galaxy(Image.open("drive/MyDrive/GalaxyClassification/training_images/121413.jpg"))

"""# Data Preprocessing"""

# removes extention from filename, in this case leaving the image id
def get_id(filename):
  id = os.path.splitext(filename)[0]
  return int(id)

# Process images into RGB pixel arrays, artificially creating new data
img_list = []
id_list = []
for filename in os.listdir(image_path):
  id = get_id(filename) # get id from filename
  single_image_path = os.path.join(image_path, filename)
  image = Image.open(single_image_path)
  image = crop_galaxy(image)

  for angle in (0,45,90,135,180,225,270,315):
    rotated_image = image.rotate(angle) # create new images through rotation
    img_list.append(img_to_array(rotated_image.resize((50,50))))
    id_list.append(id)

# Process csv, finding those with the same ids as the processed galaxies
label_list = []
for id in id_list:
  id_row = solutions.loc[solutions['GalaxyID']==id]
  elliptical = np.asarray(id_row['Class1.1'])[0]
  spiral = np.asarray(id_row['Class1.2'])[0]
  if (elliptical > spiral):
    label_list.append(np.asarray([1, 0]))
  else:
    label_list.append(np.asarray([0, 1]))

# turn lists into dataframe columns
galaxy_data = pd.DataFrame()
galaxy_data['Image_Array'] = img_list
galaxy_data['Classification'] = label_list
galaxy_data['GalaxyID'] = id_list
galaxy_data

"""# Model 1- classifying spiral galaxies from elliptical galaxies"""

x_train, x_test, y_train, y_test = train_test_split(galaxy_data['Image_Array'].to_list(),
                                                    galaxy_data['Classification'].to_list(),
                                                    test_size = .2,
                                                    random_state=42) # 80/20 rule fpr 20% test set
print("x_train size: \t", len(x_train))
print("x_test size: \t", len(x_test))
x_train[0].shape

model_1 = keras.Sequential()

model_1.add(Conv2D(64, (3, 3), input_shape=(50, 50, 3))) # filters (in powers of 2), kernel_size (square 1, 3, 5, or 7)
model_1.add(PReLU()) # Parameterized ReLU- x>0, y=x; x<0, y=ax with a as a learning coefficient
model_1.add(MaxPooling2D()) # find the most prominent features in the image and reduce dimensionality
model_1.add(Dropout(.2)) # combat overfitting by randomly droping 20% of the neurons/features

model_1.add(Conv2D(128, (3, 3))) # allows the model to find features within the image
model_1.add(PReLU())
model_1.add(MaxPooling2D()) # allows the model to be more lenient on where the the galaxy is positioned in the image
model_1.add(Dropout(.2)) #''' read paper https://jmlr.org/papers/v15/srivastava14a.html on dropout '''
model_1.add(Flatten())

model_1.add(Dense(512))
model_1.add(PReLU())

model_1.add(Dense(2, activation='softmax'))

model_1.summary()

model_1.compile(loss=keras.losses.binary_crossentropy, optimizer=keras.optimizers.Adam(learning_rate=.001), metrics=['accuracy'])
model_1.fit(np.asarray(x_train), np.asarray(y_train), epochs=50, verbose=True)

# save model (takes around 30 minutes to complete with 96% accuracy at last epoch)
model_1.save('drive/MyDrive/GalaxyClassification/Model_1')

"""# Model 1- evaluate"""

# load model
saved_model_1 = load_model('drive/MyDrive/GalaxyClassification/Model_1')
saved_model_1.summary()

# evaluate model on train and test sets
train_eval = saved_model_1.evaluate(np.asarray(x_train), np.asarray(y_train), verbose=True)
test_eval = saved_model_1.evaluate(np.asarray(x_test), np.asarray(y_test), verbose=True)
print("Train loss, accuracy: %s, %s" % (train_eval[0], train_eval[1]))
print("Test loss, accuracy: %s, %s" % (test_eval[0], test_eval[1]))

"""The numbers shown above, with 93.3% accuracy on the train set and 93.8% training on the test set, show that the model is able to generalize very well to differentiate between sprial and elliptical galaxies not in its training data."""

# evaluate the model visibly, with new data
spiral_image = Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/notBarred_2_100186.jpg')
spiral_array = img_to_array(crop_galaxy(spiral_image).resize((50, 50)))
spiral_prediction = saved_model_1.predict(np.expand_dims(spiral_array, axis=0))
print("Model_1 Prediction: " + str(format(spiral_prediction[0][0], "2f")) 
        + " spiral, " + str(format(spiral_prediction[0][1], "2f")) + " elliptical")
for layer, color in enumerate(['r','g','b']):
    pd.Series(spiral_array[:,:,layer].flatten()).plot.density(c=color)

Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/notBarred_2_100186.jpg').resize((250,250))

ell_image = Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/midE_2_108692.jpg')
ell_array = img_to_array(crop_galaxy(ell_image).resize((50, 50)))
ell_prediction = saved_model_1.predict(np.expand_dims(ell_array, axis=0))
print("Model_1 Prediction: " + str(format(ell_prediction[0][0], "2f")) 
        + " spiral, " + str(format(ell_prediction[0][1], "2f")) + " elliptical")
for layer, color in enumerate(['r','g','b']):
    pd.Series(ell_array[:,:,layer].flatten()).plot.density(c=color)

Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/midE_2_108692.jpg').resize((250,250))
# smallE_5_170648, midE_3_113516

"""# Data preprocessing for barred spirals and ellipticities"""

galaxy_data['Ellipticity'] = galaxy_data['Classification']
galaxy_data['EdgeOn_Not_or_Bar'] = galaxy_data['Classification']
for index in range(len(galaxy_data)):
  id_row = solutions.loc[solutions['GalaxyID']==galaxy_data['GalaxyID'][index]]
  elliptical = galaxy_data['Classification'][index][0]
  spiral = galaxy_data['Classification'][index][1]
  if (elliptical > spiral):
    galaxy_data.at[index, 'EdgeOn_Not_or_Bar'] = np.nan
    e0_e1 = np.asarray(id_row['Class7.1'])[0] / np.asarray(id_row['Class1.1'])[0]
    e2_e3_e4_e5 = np.asarray(id_row['Class7.2'])[0] / np.asarray(id_row['Class1.1'])[0]
    e6_e7 = np.asarray(id_row['Class7.3'])[0] / np.asarray(id_row['Class1.1'])[0]
    if ((e0_e1 > e2_e3_e4_e5) and (e0_e1 > e6_e7)):
      galaxy_data.at[index, 'Ellipticity'] = np.asarray([1, 0, 0])
    elif ((e2_e3_e4_e5 > e0_e1) and (e2_e3_e4_e5 > e6_e7)):
      galaxy_data.at[index, 'Ellipticity'] = np.asarray([0, 1, 0])
    else:
      galaxy_data.at[index, 'Ellipticity'] = np.asarray([0, 0, 1])
  else:
    galaxy_data.at[index, 'Ellipticity'] = np.nan
    edge_on = np.asarray(id_row['Class2.1'])[0] / np.asarray(id_row['Class1.2'])[0]
    if (edge_on > (np.asarray(id_row['Class2.2'])[0] / np.asarray(id_row['Class1.2'])[0])):
      galaxy_data.at[index, 'EdgeOn_Not_or_Bar'] = np.asarray([1, 0, 0])
    else:
      bar = np.asarray(id_row['Class3.1'])[0] / (np.asarray(id_row['Class2.2'])[0] + .00001)
      if (bar > (np.asarray(id_row['Class3.2'])[0] / (np.asarray(id_row['Class2.2'])[0] + .00001))):
        galaxy_data.at[index, 'EdgeOn_Not_or_Bar'] = np.asarray([0, 0, 1])
      else:
        galaxy_data.at[index, 'EdgeOn_Not_or_Bar'] = np.asarray([0, 1, 0])
galaxy_data

mask = galaxy_data['Ellipticity'].isnull()
spiral_data = galaxy_data[mask]
elliptical_data = galaxy_data[~mask]
spiral_data

"""# Model 2- classifying edge on spirals (unable to tell if barred), non-barred spirals, and barred spirals"""

x_bar_train, x_bar_test, y_bar_train, y_bar_test = train_test_split(spiral_data['Image_Array'].to_list(),
                                                                    spiral_data['EdgeOn_Not_or_Bar'].to_list(),
                                                                    test_size = .2,
                                                                    random_state = 42)
print("x_bar_train size: \t", len(x_bar_train))
print("x_bar_test size: \t", len(x_bar_test))

model_bar = keras.Sequential()
model_bar.add(Conv2D(64, (3, 3), input_shape=(50, 50, 3))) # filters (in powers of 2), kernel_size (square 1, 3, 5, or 7)
model_bar.add(PReLU()) # Parameterized ReLU- x>0, y=x; x<0, y=ax with a as a learning coefficient
model_bar.add(MaxPooling2D()) # find the most prominent features in the image and reduce dimensionality
model_bar.add(Dropout(.2)) # combat overfitting by randomly droping 20% of the neurons/features

model_bar.add(Conv2D(128, (3, 3))) # allows the model to find features within the image
model_bar.add(PReLU())
model_bar.add(MaxPooling2D()) # allows the model to be more lenient on where the the galaxy is positioned in the image
model_bar.add(Dropout(.2)) #''' read paper https://jmlr.org/papers/v15/srivastava14a.html on dropout '''
model_bar.add(Flatten())

model_bar.add(Dense(512))
model_bar.add(PReLU())

model_bar.add(Dense(3, activation='softmax'))

model_bar.summary()

model_bar.compile(loss=keras.losses.binary_crossentropy, optimizer=keras.optimizers.Adam(learning_rate=.001), metrics=['accuracy'])
model_bar.fit(np.asarray(x_bar_train), np.asarray(y_bar_train), epochs=50, verbose=True)

# save model (takes around 30 minutes to complete with 96% accuracy at last epoch)
model_bar.save('drive/MyDrive/GalaxyClassification/Model_Bar')

"""# Model 2- evaluate"""

# load model
saved_model_bar = load_model('drive/MyDrive/GalaxyClassification/Model_Bar')
saved_model_bar.summary()

# evaluate model on train and test sets
train_eval_bar = saved_model_bar.evaluate(np.asarray(x_bar_train), np.asarray(y_bar_train), verbose=True)
test_eval_bar = saved_model_bar.evaluate(np.asarray(x_bar_test), np.asarray(y_bar_test), verbose=True)
print("Train loss, accuracy: %s, %s" % (train_eval_bar[0], train_eval_bar[1]))
print("Test loss, accuracy: %s, %s" % (test_eval_bar[0], test_eval_bar[1]))

def single_image_eval_bar(image_path):
  sieb_image = Image.open(image_path)
  sieb_array = img_to_array(crop_galaxy(sieb_image).resize((50, 50)))
  sieb_prediction = saved_model_bar.predict(np.expand_dims(sieb_array, axis=0))
  print("Model_1 Prediction: " + str(format(sieb_prediction[0][0], "2f")) 
         + " edge on, " + str(format(sieb_prediction[0][1], "2f")) + " not barred, "
         + str(format(sieb_prediction[0][2], "2f")) + " barred")
  for layer, color in enumerate(['r','g','b']):
      pd.Series(sieb_array[:,:,layer].flatten()).plot.density(c=color)

# barred spiral
single_image_eval_bar('drive/MyDrive/GalaxyClassification/eval_images/names_set/barred_2_171436.jpg')

Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/barred_2_171436.jpg').resize((250,250))

# not barred spiral
single_image_eval_bar('drive/MyDrive/GalaxyClassification/eval_images/names_set/notBarred_1_182971.jpg')

Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/notBarred_1_182971.jpg').resize((250,250))

# edge on spiral
single_image_eval_bar('drive/MyDrive/GalaxyClassification/eval_images/names_set/edgeOn_1_107946.jpg')

Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/edgeOn_1_107946.jpg').resize((250,250))

"""# Model 3- classifying galaxies based on ellipticity (E0-1, E2-5, E6-7)"""

x_ell_train, x_ell_test, y_ell_train, y_ell_test = train_test_split(elliptical_data['Image_Array'].to_list(),
                                                                    elliptical_data['Ellipticity'].to_list(),
                                                                    test_size = .2,
                                                                    random_state = 42)
print("x_ell_train size: \t", len(x_ell_train))
print("x_ell_test size: \t", len(x_ell_test))

model_ell = keras.Sequential()
model_ell.add(Conv2D(64, (3, 3), input_shape=(50, 50, 3))) # filters (in powers of 2), kernel_size (square 1, 3, 5, or 7)
model_ell.add(PReLU()) # Parameterized ReLU- x>0, y=x; x<0, y=ax with a as a learning coefficient
model_ell.add(MaxPooling2D()) # find the most prominent features in the image and reduce dimensionality
model_ell.add(Dropout(.2)) # combat overfitting by randomly droping 20% of the neurons/features

model_ell.add(Conv2D(128, (3, 3))) # allows the model to find features within the image
model_ell.add(PReLU())
model_ell.add(MaxPooling2D()) # allows the model to be more lenient on where the the galaxy is positioned in the image
model_ell.add(Dropout(.2)) #''' read paper https://jmlr.org/papers/v15/srivastava14a.html on dropout '''
model_ell.add(Flatten())

model_ell.add(Dense(512))
model_ell.add(PReLU())

model_ell.add(Dense(3, activation='softmax'))

model_ell.summary()

model_ell.compile(loss=keras.losses.binary_crossentropy, optimizer=keras.optimizers.Adam(learning_rate=.001), metrics=['accuracy'])
model_ell.fit(np.asarray(x_ell_train), np.asarray(y_ell_train), epochs=50, verbose=True)

# save model (takes around 30 minutes to complete with 96% accuracy at last epoch)
model_ell.save('drive/MyDrive/GalaxyClassification/Model_Ell')

"""# Model 3- evaluate"""

# load model
saved_model_ell = load_model('drive/MyDrive/GalaxyClassification/Model_Ell')
saved_model_ell.summary()

# evaluate model on train and test sets
train_eval_ell = saved_model_ell.evaluate(np.asarray(x_ell_train), np.asarray(y_ell_train), verbose=True)
test_eval_ell = saved_model_ell.evaluate(np.asarray(x_ell_test), np.asarray(y_ell_test), verbose=True)
print("Train loss, accuracy: %s, %s" % (train_eval_ell[0], train_eval_ell[1]))
print("Test loss, accuracy: %s, %s" % (test_eval_ell[0], test_eval_ell[1]))

def single_image_eval_ell(image_path):
  siee_image = Image.open(image_path)
  siee_array = img_to_array(crop_galaxy(siee_image).resize((50, 50)))
  siee_prediction = saved_model_ell.predict(np.expand_dims(siee_array, axis=0))
  print("Model_1 Prediction: " + str(format(siee_prediction[0][0], "2f")) 
         + " E0 or E1, " + str(format(siee_prediction[0][1], "2f")) + " E2 to E5, "
         + str(format(siee_prediction[0][2], "2f")) + " E6 or E7")
  for layer, color in enumerate(['r','g','b']):
      pd.Series(siee_array[:,:,layer].flatten()).plot.density(c=color)

# small E
single_image_eval_ell('drive/MyDrive/GalaxyClassification/eval_images/names_set/smallE_1_114457.jpg')

Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/smallE_1_114457.jpg').resize((250,250))

# mid E
single_image_eval_ell('drive/MyDrive/GalaxyClassification/eval_images/names_set/midE_1_175254.jpg')

Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/midE_1_175254.jpg').resize((250,250))

# large E
single_image_eval_ell('drive/MyDrive/GalaxyClassification/eval_images/names_set/largeE_2_100740.jpg')

Image.open('drive/MyDrive/GalaxyClassification/eval_images/names_set/largeE_2_100740.jpg').resize((250,250))
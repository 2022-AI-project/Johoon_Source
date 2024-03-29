from PIL import Image
import os, glob, numpy as np
from numpy import ndarray as nda
from sklearn.model_selection import train_test_split

class make_model():
    def __init__(self):
        self.categories = ["apple", "carrot", "orientalmelon", "strawberry", "tomato", "watermelon"]
        self.nb_classes = len(self.categories)
        self.image_w = 128   # width of image
        self.image_h = 128   # height of image

        self.image_rotate()     # 전처리 완료 시 생략 
        self.make_npy_file()    # 전처리 완료 시 생략 
        self.make_model()

    # train data image 를 rotate 하는 method -> Data augmentation
    def image_rotate(self):
        caltech_dir = "./multi_img_data/imgs_others/train"          # train data directory
        saving_dir = "./multi_img_data/imgs_others/train_rotated"   # rotated train data directory
        # 6 categories -> 6 classes (6 labels)

        for idx, cat in enumerate(self.categories):     # 현재 6 개의 label 들에 대한 train data를 수집한다.
            image_dir = caltech_dir + "/" + cat         # 각 label 들의 train data image 는 caltech_dir에
            files = glob.glob(image_dir + "/*.png")     #   그 label 이름의 directory 내부에 *.png 파일로 저장되어 있다.
                                                        #   모든 *.png 파일을 files 에 저장한다.
            print(cat, "사진 개수 : ", len(files))       # 현재 label 의 train data image 의 개수를 출력한다.
            for i, f in enumerate(files):               #   모든 *.png 파일을 하나하나 작업을 진행한다.
                img = Image.open(f)                     # img 로 현재 파일을 정의한 후
                img = img.convert("RGB")                #   현재 image 를 RGB mode 로 변경한다.
                img = img.resize((self.image_w, self.image_h))      # 현재 image 를 128 * 128 size 로 resizing 한다.
                                                                    # Data augmentation 에 해당된다.
                white = (255, 255, 255)                 # 하얀색은 RGB로 [255, 255, 255] 이다.

                for j in range(-9, 9):                      # -180도 부터 20도씩 증가하여 160도까지 Image Rotation 을 진행한다.
                    img_name = f.split('.')
                    img_name = img_name[1].split("\\")

                    img_ro = img.rotate(20 * j, expand = 1, fillcolor = white)  # `20 * j` 부분에서 20도 기준으로 돌아가도록 구현되었다.
                    img_ro = img_ro.crop((img_ro.size[0]/2 - self.image_w/2, img_ro.size[1]/2 - self.image_h/2, img_ro.size[0]/2 + self.image_w/2, img_ro.size[1]/2 + self.image_h/2))
                    finally_saving_dir = saving_dir + "/" + cat + "/" + img_name[1] + "_" + str(j + 10) + ".png"
                    img_ro.save(finally_saving_dir)

    # Dataset을 가지고 *.npy file 을 만드는 method 이다.
    def make_npy_file(self):
        # rotate 된 train data image 가 있는 directory
        caltech_dir_rotated = "./multi_img_data/imgs_others/train_rotated"

        X = []
        y = []

        for idx, cat in enumerate(self.categories):                     # Category 순서대로 Dataset 을 불러온다.
            # 현재 label target score 를 정의한다.
            label = [0 for i in range(self.nb_classes)]                 # Category 순서대로 label 을 만든 뒤
            label[idx] = 1                                              #   현재 label에 해당되는 부분만 1로 만든다.

            image_dir_rotated = caltech_dir_rotated + "/" + cat         # 현재 label에 해당되는 Dataset이 있는 directory 이다.
            files = glob.glob(image_dir_rotated + "/*.png")             # 그 directory에 있는 모든 *.png 파일들 이다.

            print(" ", label, " data 개수 :", len(files))
        
            for i, f in enumerate(files):                               # 불러온 모든 Dataset file 들을
                img = Image.open(f)                                     # 하나하나 open 하고
                # img = img.convert("RGB")
                # img = img.resize((self.image_w, self.image_h))
                data = np.asarray(img)                                  # data화 한다.
               
                X.append(data)      # 현재 image data 를 append 한다.
                y.append(label)     # 현재 image 의 target score 를 append 한다.

        X = np.array(X)
        y = np.array(y)

        X_train, X_test, y_train, y_test = train_test_split(X, y)   # train, validation set으로 나뉜다.
                                                                    # 임의의 25%의 Data가 validation set 으로 나뉜다.
        xy = (X_train, X_test, y_train, y_test)                     # train, validation data 를 xy 에 저장한다.
        np.save("./numpy_data/multi_image_data.npy", xy)            # 그 xy를 통해 *.npy 파일을 생성한다.

    def make_model(self):
        import tensorflow as tf
        from tensorflow import keras
        from keras.models import Sequential
        from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Dropout
        from keras.callbacks import EarlyStopping, ModelCheckpoint
        from keras.optimizers import Adam, Nadam
        import matplotlib.pyplot as plt
        import keras.backend.tensorflow_backend as K

        config = tf.compat.v1.ConfigProto()     # Configuration
        config.gpu_options.allow_growth = True

        X_train, X_test, y_train, y_test = np.load("./numpy_data/multi_image_data.npy", allow_pickle = True)
        
        X_train = X_train.astype(float) / 255   # 현재 Input train data의 모든 element 값을 255로 나눈다.
        X_test = X_test.astype(float) / 255     # 현재 Input test data의 모든 element 값을 255로 나눈다.

        '''
        1. 사용된 parameter 의 총 개수를 얻어보자.
        '''
        with K.tf_ops.device('/device:CPU:0'):
            model = Sequential()                                                                            # CNN 을 통해 model 을 만들 것 이다.
            
            model.add(Conv2D(32, (3, 3), padding="same", input_shape=X_train.shape[1:], activation='relu')) # 3x3 Conv, 32 filters, 공간정보 유지, relu
            model.add(MaxPooling2D(pool_size=(2, 2)))                                                       # 2x2 maxPooling, 공간이 1/2 로 줄어든다.
            model.add(Dropout(0.25))                                                                        # 25% 확률로 dropout을 진행한다.

            model.add(Conv2D(64, (3, 3), padding="same", activation='relu'))                                # 3x3 Conv, 64 filters, 공간정보 유지, relu
            model.add(MaxPooling2D(pool_size=(2, 2)))                                                       # 2x2 maxPooling, 공간이 1/2 로 줄어든다.
            model.add(Dropout(0.25))                                                                        # 25% 확률로 dropout을 진행한다.

            model.add(Flatten())                                                                            # 현재 map 을 flatten 한다.
            model.add(Dense(256, activation='relu'))                                                        # 1*1*256 으로 dense 시킨다.
            model.add(Dropout(0.5))                                                                         # 50% 확률로 dropout을 진행한다.
            model.add(Dense(self.nb_classes, activation='softmax'))                                         # class의 개수만큼 차원의 벡터를 출력한다.
 
            optimizer=Adam(learning_rate = 0.001)
            model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])
     

            model_dir = './model'               # model 이 저장되는 directory 이다.

            if not os.path.exists(model_dir):   # model_dir 이 존재하지 않는다면
                os.mkdir(model_dir)             #   model_dir 을 미리 만든다.

            model_path = model_dir + '/multi_img_classification.model'   # model 은 model_dir 에 좌측과 같은 이름으로 생성된다.
            checkpoint = ModelCheckpoint(filepath=model_path, monitor='val_loss',   # 현재 model을 저장한다.
                                         verbose=1, save_best_only=True)
            
            early_stopping = EarlyStopping(monitor='val_loss', patience=600)         # validation loss 값이 6개의 연속된 epoch 에서 더이상 나아지지 않을때 stop 한다.

        model.summary() # model 의 각 layer 들을 파악한다.

        # batch size 와 epoch 수를 정하여 model.fit 을 실행한다.
        history = model.fit(X_train, y_train, batch_size=128, epochs=50, validation_data=(X_test, y_test), callbacks=[checkpoint, early_stopping])
        
        print("정확도 : %.4f" % (model.evaluate(X_test, y_test)[1]))

        y_vloss = history.history['val_loss']
        y_loss = history.history['loss']
        
        y_vacc = history.history['val_accuracy']
        y_acc = history.history['accuracy']

        print("y vLoss :", y_vloss)

        x_len = np.arange(len(y_loss))

        # Loss function 과 Accuracy function 을 출력한다.
        plt.figure(1)
        plt.plot(x_len, y_vloss, marker='.', c='red', label='val_set_loss')
        plt.plot(x_len, y_loss, marker='.', c='blue', label='train_set_loss')
        plt.legend()
        plt.xlabel('epochs')
        plt.ylabel('loss')
        plt.grid()
        
        plt.figure(2)
        plt.plot(x_len, y_vacc, marker='.', c='red', label='val_set_acc')
        plt.plot(x_len, y_acc, marker='.', c='blue', label='train_set_acc')
        plt.legend()
        plt.xlabel('epochs')
        plt.ylabel('accuracy')
        plt.grid()
        
        plt.show()

if __name__ == '__main__':
    w = make_model()
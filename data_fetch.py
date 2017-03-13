import os
from os import listdir
from os.path import isfile, join
from shutil import copyfile

import librosa

from bs4 import BeautifulSoup
import urllib
import tarfile
import numpy as np
import utils
import wave

# url = 'http://www.repository.voxforge1.org/downloads/SpeechCorpus/Trunk/Audio/Original/48kHz_16bit/'
url = 'http://www.repository.voxforge1.org/downloads/SpeechCorpus/Trunk/Audio/Main/16kHz_16bit/'


def fetch_data():
    page = urllib.urlopen(url)
    soup = BeautifulSoup(page)

    for link in soup.find_all('a'):
        link_url = link.get('href')
        extension = link_url.split('.')[-1]
        if extension == 'tgz':
            name = link_url.split('.')[-2]
            download_url = url + link.get('href')
            print(download_url)
            file_name = 'raw_sound/' + name + '.' + extension
            urllib.urlretrieve(download_url, file_name)
            tar = tarfile.open(file_name)
            tar.extractall('raw_sound/')


def inspect():
    dialect_dict = {}
    i = 0
    j = 0
    k = 0
    for root, dirs, files in os.walk('raw_sound/'):
        i += 1
        if os.path.basename(root) != 'etc':
            continue
        for f in files:
            if not f.startswith('README'):
                continue
            with open(os.path.join(root, f)) as fp:
                k += 1
                data = fp.read()
                try:
                    idx = data.index('Pronunciation dialect')
                except ValueError:
                    break
                try:
                    idx2 = data.index('Gender')
                except ValueError:
                    break
                j += 1
                fp.seek(idx)
                dialect_line = fp.readline()
                dialect_field = dialect_line.split(':')[1] if len(dialect_line.split(':')) > 0 else ''
                dialect_field = dialect_field.strip('\n')

                fp.seek(idx2)
                gender_line = fp.readline()
                gender_field = gender_line.split(':')[1] if len(gender_line.split(':')) > 0 else ''
                gender_field = gender_field.strip('\n')
                # print(gender_field)
                to_dict = dialect_field
                # to_dict = dialect_field + ' / ' + gender_field
                print(dialect_field)
                print(root, dirs)

                dialect_dict[to_dict] = dialect_dict.get(to_dict, 0) + 1
                print('parsed %s out of %s readmes out of %s files' % (j, k, i))
    dialect_tup = [(k, v) for k, v in dialect_dict.items()]
    dialect_tup = sorted(dialect_tup, key=lambda x: x[1], reverse=True)
    print(dialect_tup)


def organize():
    for root, dirs, files in os.walk('raw_sound/'):
        dirnames = [os.path.basename(d) for d in dirs]
        if len(dirnames) == 2:
            if 'wav' in dirnames and 'etc' in dirnames:
                move_subfolder(root, dirs)
            else:
                continue


def move_subfolder(root, dirs):
    readme_files, wav_files = get_dir_files(root, dirs)
    if readme_files == "" or wav_files == "":
        return

    readme = [f for f in readme_files if f.startswith('README')]
    if len(readme) != 1:
        return

    readme = readme[0]
    dialect, gender = get_dialect_gender(root, readme)

    if dialect == "" or gender == "":
        return
    target_path = get_target_folder(dialect, gender)
    if target_path == "":
        return
    wavs = [f for f in wav_files if f.endswith('.wav')]

    for wav in wavs:
        copyfile(os.path.join(root, 'wav', wav), os.path.join(target_path, wav))


def get_dir_files(root, dirs):
    readme = [d for d in dirs if d.startswith('etc')]
    wav = [d for d in dirs if d.startswith('wav')]
    if len(readme) != 1 or len(wav) != 1:
        return "", ""

    readme_dir = readme[0]
    readme_dir = os.path.join(root, readme_dir)
    readme_files = [f for f in listdir(readme_dir) if isfile(join(readme_dir, f))]

    wav_dir = wav[0]
    wav_dir = os.path.join(root, wav_dir)
    wav_files = [f for f in listdir(wav_dir) if isfile(join(wav_dir, f))]
    return readme_files, wav_files


def get_target_folder(dialect, gender, base_output_path="sorted_sound"):
    dialect_path = ""
    gender_path = ""
    if dialect.find("american") != -1:
        dialect_path = "american"
    elif dialect.find("british") != -1:
        dialect_path = "british"

    if gender.find("female") != -1:
        gender_path = "female"
    elif gender.find("male") != -1:
        gender_path = "male"

    if dialect_path != "" and gender_path != "":
        return base_output_path + "/" + dialect_path + "/" + gender_path
    return ""


def get_dialect_gender(root, f):
    with open(os.path.join(root, 'etc', f)) as fp:
        data = fp.read()
        try:
            idx = data.index('Pronunciation dialect')
        except ValueError:
            return "", ""
        try:
            idx2 = data.index('Gender')
        except ValueError:
            return "", ""
        fp.seek(idx)
        dialect_line = fp.readline()
        dialect_field = dialect_line.split(':')[1] if len(dialect_line.split(':')) > 0 else ''
        dialect_field = dialect_field.strip('\n')
        dialect_field = dialect_field.strip(' ')
        dialect_field = dialect_field.lower()

        fp.seek(idx2)
        gender_line = fp.readline()
        gender_field = gender_line.split(':')[1] if len(gender_line.split(':')) > 0 else ''
        gender_field = gender_field.strip('\n')
        gender_field = gender_field.strip(' ')
        gender_field = gender_field.lower()

        return dialect_field, gender_field


def cut():
    # utils.slice('organized_sound/wav/british/bo156.wav', 'test.wav', 0, 3000)
    base_dir = 'organized_sound/wav/'
    language_dirs = ['american', 'british']
    for language in language_dirs:
        lang_dir_path = base_dir + language + '/'
        for filename in os.listdir(base_dir + language):
            if filename.endswith('.wav'):
                filepath = lang_dir_path + filename
                outpath = lang_dir_path + 's_' + filename
                infile = wave.open(filepath)
                utils.slice(infile, outpath, 0, 3000)


def preprocess(sound_path):
    folders = [f for f in listdir(sound_path) if not isfile(join(sound_path, f))]
    classes = len(folders)
    data_list = []
    label_list = []
    for folder_ix, folder in enumerate(folders):
        sub_path = join(sound_path, folder)
        onlyfiles = [f for f in listdir(sub_path) if isfile(join(sub_path, f)) and not f.startswith('.DS')]

        for ix, audio_file in enumerate(onlyfiles):
            x, fs = librosa.load(join(sub_path, audio_file))
            S, fs = utils.read_audio_spectrum(x, fs)
            formatted_vec = np.ascontiguousarray(S.T[None, None, :, :])
            data_list.append(formatted_vec)
        label_list.append(np.ones([len(onlyfiles), 1]) * folder_ix)

    Ys = np.concatenate(label_list)

    specX = np.zeros([len(data_list), 130, 1025])
    for i, x in enumerate(data_list):
        specX[i] = x

    data_and_label = [[specX[i, :, :], Ys[i]] for i in range(len(data_list))]
    split1 = specX.shape[0] - specX.shape[0] / 5
    split2 = (specX.shape[0] - split1) / 2

    shuffled_data = np.random.permutation(data_and_label)
    shuffled_x = [a[0] for a in shuffled_data]
    shuffled_y = [a[1] for a in shuffled_data]
    trainX, otherX = np.split(shuffled_x, [split1])
    trainYa, otherY = np.split(shuffled_y, [split1])
    valX, testX = np.split(otherX, [split2])
    valYa, testYa = np.split(otherY, [split2])

    trainY = to_one_hot(trainYa)
    testY = to_one_hot(testYa)
    valY = to_one_hot(valYa)
    return classes, trainX, trainY, valX, valY, testX, testY


def to_one_hot(Y):
    res = []
    for y in Y:
        if y == 0:
            res.append([1, 0])
        if y == 1:
            res.append([0, 1])
    return res


if __name__ == '__main__':
    # fetch_data()
    # inspect()
    organize()
    # cut()
    # preprocess('organized_sound/wav/')

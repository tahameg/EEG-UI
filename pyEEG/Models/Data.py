import pyedflib
import numpy
import random
import sqlite3
import uuid

def get_freq(_file):
    n_channel = len(_file.getNSamples())
    f_sampler = []
    for i in range(0, 3):
        f_sampler.append(_file.getSampleFrequency(random.randint(0, n_channel-1)))
    for i in range(0, 2):
        if f_sampler[i] != f_sampler[i + 1]:
            raise Exception("Invalid Data: All channels must be recorded with the same frequency!")
        else:
            return f_sampler[i]


def get_n_samples(_file):
    n_channel = len(_file.getNSamples())
    f_sampler = []
    for i in range(0, 3):
        f_sampler.append(_file.getNSamples()[random.randint(0, n_channel-1)])
    for i in range(0, 2):
        if f_sampler[i] != f_sampler[i + 1]:
            raise Exception("Invalid Data: All channels must include same number of data points!")
        else:
            return f_sampler[i]


def prefilter2Dict(prefilter):
    return_dict = {}
    x = prefilter.split()
    for i in x:
        y = i.split(":")
        return_dict[y[0]] = int(y[1][0:-2])
    return return_dict


def dict2Prefilter(dict):
    return_string = ""
    for key, val in dict:
        return_string += (key+":"+val+" ")
    return return_string[0:-1]


def makeUniqueList(input): # return a list of uniq
    return_list = []
    for i in input:
        if i not in return_list:
            return_list.append(i)
    return return_list

def getClosestIndex(array, value):
    """
    get index of element that is closest to the value
    :param list:
    :param value:
    :return:
    """
    return (numpy.abs(array-value)).argmin()

def makeAnnotation(tag, desc):
    return {
        "tag" : tag,
        "description" : desc
            }

def makeEpoch(annotation, lower_time, upper_time, time_array):
    """
    make an epoch object:
        {"low-time-idx" : float,
         "high-time-idx" : float,
         "annotation" : {
                "tag" : " ",
                "description" : " "
                }
            }
    :param annotation: use makeAnnotation function for creating this
    :param lower_time: time when the event starts
    :param upper_time: time when the event ends
    :param time_array: the time array
    :return:
    """
    return {"low-time-idx" : getClosestIndex(time_array, lower_time),
            "high-time-idx" : getClosestIndex(time_array, upper_time),
            "annotation" : annotation
            }



class Dataset:
    def __init__(self, _name, _file):
        self.File = _file
        self.ID = uuid.uuid4()
        self.Name = _name
        self.Filename = _file.file_name
        self.NChannel = _file.getNSamples()
        self.Freq = get_freq(_file)
        self.NSamples = get_n_samples(_file)
        self.Duration = self.NSamples/self.Freq
        self.AnnotationTags = makeUniqueList(_file.readAnnotations()[2])
        self.Epochs = []
        self.Time = numpy.arange(0, self.Duration, 1/self.Freq)
        self.Header = Header(_file.getHeader())

    def _createAnnotations(self, descriptions):
        return_list = []
        for t in range(0, len(self.AnnotationTags)):
            return_list.append(makeAnnotation(self.AnnotationTags[t], descriptions[t]))
        return return_list

    def createEpochs(self, descriptions):
        annotations = self._createAnnotations(descriptions)
        annotations_raw = self.File.readAnnotations()
        event_num = len(annotations_raw[0])
        for i in range(0, event_num):
            for a in annotations:
                if annotations_raw[2][i] == a["tag"]:
                    self.Epochs.append(makeEpoch(a, annotations_raw[0][i], annotations_raw[0][i]+annotations_raw[1][i], self.Time))

class Header:
    def __init__(self, _header_dict):
        """
        create Header object for storing header data. Header information is given as dictionary.
        (see Header.getEmptyDict() for valid header dict)
        :param _header_dict:
        Header Dictionary
        """
        self.Header = _header_dict
        try:
            self.technician = self.Header['technician']
            self.recording_additional = self.Header["recording_additional"]
            self.patientname = self.Header["patientname"]
            self.patient_additional = self.Header["patient_additional"]
            self.patientcode = self.Header["patientcode"]
            self.equipment = self.Header["equipment"]
            self.admincode = self.Header["admincode"]
            self.gender = self.Header["gender"]
            self.startdate = self.Header["startdate"]
            self.birthdate = self.Header["birthdate"]
        except:
            raise Exception("invalid Header dictionary structure is given as parameter. (see Header.getEmptyDict() for valid header dict)")


    @staticmethod
    def getEmptyDict():
        returnVal = {'technician': '',
                     'recording_additional': '',
                     'patientname': '',
                     'patient_additional': '',
                     'patientcode': '',
                     'equipment': '',
                     'admincode': '',
                     'gender': '',
                     'startdate': None,
                     'birthdate': ''}
        return returnVal

    def getDict(self):
        self.Header = {'technician': self.technician,
                     'recording_additional': self.recording_additional,
                     'patientname': self.patientname,
                     'patient_additional': self.patient_additional,
                     'patientcode': self.patientcode,
                     'equipment': self.equipment,
                     'admincode': self.admincode,
                     'gender': self.gender,
                     'startdate': self.startdate,
                     'birthdate': self.birthdate}
        return self.Header

class Channel:
    def __init__(self, _idx, _channel_dict):
        """
        create Channel object for storing Channel data. Channel information is given as dictionary.Index of the given channel must be provided
        (see Header.getEmptyChannel() for valid channel dict)
        :param _header_dict:
        Header Dictionary
        """
        try:
           self.label = _channel_dict["label"]
           self.dimension = _channel_dict["dimension"]
           self.physical_max = _channel_dict["physical_max"]
           self.physical_min = _channel_dict["physical_min"]
           self.digital_max = _channel_dict["digital_max"]
           self.digital_min = _channel_dict["digital_min"]
           self.prefilter = prefilter2Dict(_channel_dict["prefilter"])
           self.transducer = _channel_dict["transducer"]
        except:
            raise Exception("invalid Header file structure is given as parameter. (see Channel.getEmptyDict() for valid header dict)")


    @staticmethod
    def getEmptyDict():
        return {'label': '',
                'dimension': '',
                'sample_rate': 0,
                'physical_max': 0,
                'physical_min': 0,
                'digital_max': 0,
                'digital_min': 0,
                'prefilter': "HP:0HZ LP:0HZ N:0HZ",
                'transducer': ''}

    def getDict(self, sample_rate):
        return {'label': self.label,
                'dimension': self.dimension,
                'sample_rate': sample_rate,
                'physical_max': self.physical_max,
                'physical_min': self.physical_min,
                'digital_max': self.digital_max,
                'digital_min': self.digital_min,
                'prefilter': dict2Prefilter(self.prefilter),
                'transducer': self.transducer
                }

class Signal:
    def __init__(self, _channel, ):
        self.channel = _channel
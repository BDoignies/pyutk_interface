import os
import uuid
import subprocess
import tempfile
import numpy as np

__UTK__DIR__ = ""
__UTK__WDIR__ = tempfile.gettempdir()
__UTK__SILENCE__ = True


def set_dir(dir):
    """
        Set UTK Directory

        Parameters
        ----------
            dir: str
                The path where the built utk is located
    """
    global __UTK__DIR__
    if not os.path.exists(dir):
        raise FileNotFoundError(f"{os.path.abspath(dir)} does not exists")

    __UTK__DIR__ = dir

def set_wdir(dir):
    """
        Set working directory

        As this file is just a wrapper around utk exe
        it needs a place to store generated files

        Parameters
        ----------
            dir: src
                The path to the working directory. Not that
                it is created if needed
    """
    if not os.path.exists(dir):
        os.mkdir(dir)
    __UTK__DIR__ = dir

def set_silence(silence=True):
    """
        Sets silence mode for samplers

        Note that for some reason some samplers
        still outputs data to the console.

        Parameters
        ----------
            silence: bool
                True to silence (most) outputs.
    """
    global __UTK__SILENCE__
    __UTK__SILENCE__ = silence

def get_samplers_dir():
    """
        Return the directory where the samplers exe are

        Returns
        -------
            str
                The path where the samplers are located
    """
    return os.path.join(__UTK__DIR__, "samplers")

def get_discrepancy_dir():
    """
        Returns the discrepancy directory

        Returns
        -------
            str
                The path where the discrepancy exe are located
    """
    return os.path.join(__UTK__DIR__, "discrepancy")

def get_silence_args():
    """
        Return the argument to pass to silence (or not) the sampler 

        Returns
        -------
            list
                Arguments to pass to silence (or not) the sampler
    """
    if __UTK__SILENCE__:
        return ["--silent"]
    return []

def get_samplers(split_i_d=False):
    """
        Returns the list of availaible samplers

        The returns is a dictionnary where each sampler
        maps to a set of available dimensions.  
        If `split_i_d` is set to true, an additional level
        will be added.

        Parameters
        ----------
            split_i_d: bool [default=False]
                When set to true, the 'dd' and 'di' suffixes are 
                treated as different. When false, they are merged
                together.

        Returns
        -------
            dict
                A dictionnary mapping sampler name to the 
                set of available dimension. 
    """
    samplers = {}
    for file in os.listdir(get_samplers_dir()):
        filepath = os.path.join(get_samplers_dir(), file)
        is_sampler = os.access(filepath, os.X_OK) and \
                     not os.path.isdir(filepath) and \
                     ("dd" in filepath or "di" in filepath)
        if is_sampler:
            sampler_info = file.split("_")
            sampler_name = "_".join(sampler_info[:-1])
            
            try:
                dim = int(sampler_info[-1][:-2])
                
                if sampler_name not in samplers:
                    if split_i_d:
                        samplers[sampler_name] = {}
                    else:
                        samplers[sampler_name] = set()
                
                if split_i_d:
                    if "d" not in samplers[sampler_name]:
                        samplers[sampler_name]["d"] = set()
                    if "i" not in samplers[sampler_name]:
                        samplers[sampler_name]["i"] = set()
                        
                    if sampler_info[1].endswith("dd"):
                        samplers[sampler_name]["d"].append(dim)

                    if sampler_info[1].endswith("di"):
                        samplers[sampler_name]["i"].append(dim)
                else:
                    samplers[sampler_name].add(dim)
            except Exception as e:
                pass

    if not split_i_d:
        for name in samplers:
            samplers[name] = sorted(samplers[name])
    else:
        for name in samplers:
            samplers[name]["d"] = sorted(samplers[name]["d"])

    return samplers


class PointReader:
    """
        Read points points of a files   

        Parameters
        ----------
            n: int
                The number of points to read. It must also be the number of
                line in read files
            d: int
                The dimension of each poitn
            sep: str [default="\t"]
                The separator between each coordinate
    """
    def __init__(self, n, d, sep="\t"):
        self.n = n
        self.d = d
        self.sep = sep

    def read(self, filepath):
        """
            Read the content of a file to an array
    
            The extension is used to determine the underlying
            format. If it ends with ".dat" the files is read 
            as text. Otherwise it is read as binary. 

            Parameters
            ----------
                filepath: str
                    Path to the file to read
            Returns
            -------
                np array
                    An array of shape (n, d) with each points filled    
        """
        if os.path.splitext(filepath)[1] == ".dat":
            return self.read_text(filepath)
        
        return self.read_bin(filepath)

    def read_bin(self, filepath):
        """
            Read the content of a binary file to an array
    
            The first 4 bytes are skipped as they represent
            the number of points and it is already known. 

            Parameters
            ----------
                filepath: str
                    Path to the file to read
            Returns
            -------
                np array
                    An array of shape (n, d) with each points filled    
        """
        points = np.empty((self.n, self.d), dtype=np.double)
        points = np.fromfile(filepath, dtype=">d", offset=4)
        return points.reshape((self.n, self.d))

    def read_text(self, filepath):
        """
            Read the content of a file to an array
    
            Parameters
            ----------
                filepath: str
                    Path to the file to read

            Returns
            -------
                np array
                    An array of shape (n, d) with each points filled    
        """
        points = np.empty((self.n, self.d), dtype=np.double)
        with open(filepath, "r") as file:
            for i, point in enumerate(file):
                coords = list(map(np.double, point.strip().split(self.sep)))
                points[i] = coords
        
        return points

class PointWriter:
    """
        Writer compatible with UTK.

        Parameters
        ----------
            file: str [defailt=None]
            sep: char [default='\t']
            pointset_sep: char [default='#']
            append: bool [default=True]
    """
    def __init__(self, file=None, sep='\t', pointset_sep="#", append=True):
        self.sep = sep
        self.pointset_sep = pointset_sep
        self.append = append
        self.open_mode = 'a+' if append else 'w+'
    
        self.file = None
        if file is not None:
            self.open(file)
    
    def open(self, outFile):
        if self.file is not None:
            self.close()

        self.file = open(outFile, self.open_mode)
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __write_points(self, file, points):
        """
            Writes a pointset to file

            Parameters
            ==========
                file: file
                    The file to write to
                points: np array like
                    The points to write
        """
        points = points.astype(str)
        for point in points:
            file.write(self.sep.join(point.tolist()))
            file.write("\n")

    def __process_header(self, file):
        if self.append:
            current = self.file.tell()
            # Nothing in the file yet
            if current == 0:
                return
            
            self.file.seek(current -1)
            current_char = self.file.read(1)
            self.file.seek(current)

            if current_char != '\n':
                self.file.write('\n')
            self.file.write(self.pointset_sep)
            self.file.write('\n')

    def write(self, points=np.asarray([[]])):
        """ 
            Writes the points to a file

            For now, only text files is supported.

            Parameters
            ----------
                outfile: str
                    The path to file to write
                points: np array like
                    The points to write
        """
        if points.ndim == 2:
            self.__process_header(self.file)
            self.__write_points(self.file, points)
        else:
            for p in points:
                self.__write_points(self.file, p)
                self.file.write(self.pointset_sep)
                self.file.write("\n")

    def close(self):
        """
            Close the file
        """
        self.file.close()
        self.file = None
                
class DiscrepancyReader:
    """
        Read points points of a files   

        Parameters
        ----------
            sep: str [default="\t"]
                The separator between each coordinate
            exclude_char: int [default=1]
                The number of character to exclude at the beginning of the name
    """
    def __init__(self, sep="\t", exculde_char=1):
        self.sep = sep
        self.exclude = exculde_char

    def read(self, filepath):
        """
            Read the content of a file to an array of dictionnaries

            The first line is supposed to contain names of the output and 
            subsequent lines the results. 

            Example: 
            #Nbpts		#Mean		#Var		#Min		#Max		#NbPtsets
            1024		0.00117859		0		0.00117859		0.00117859		1

            Empty results or names are taken away so the format must be consistent
            between each lines. Each name (in lower case) will be a key in the 
            resulting dictionnaries. 

            Parameters
            ----------
                filepath: str
                    The file to read

            Result
                list
                    A list of dictionnaries containing the results    
        """
        results = []
        with open(filepath, "r") as file:
            names = file.readline()
            names = names.strip().split(self.sep)
            names = [name[self.exclude:].lower() for name in names if name]

            for line in file:
                splitted = line.strip().split(self.sep)
                splitted = [splitted_ for splitted_ in splitted if splitted_]

                result = {}
                for name, value in zip(names, splitted):
                    result[name] = np.double(value)
                results.append(result)
        return results
    
class Sampler:
    """
        Interface to UTK Sampler
        
        This class encapsulate details to run a sampler of the utk libary

        Parameters
        ----------
            name: str
                The name of the sampler
            d: int
                The dimension of the point generated by the sampler
            index: str [default='d']
                Prefix to the sample name (either 'i' or 'd')
            **kwargs:
                Additionnal information for the sampler
    """
    def __init__(self, name, d, index='d', **kwargs):
        self.name = name
        self.d = d
        self.exename = name + f"_{d}d{index}"
        self.args = [
            str(item)
            for items in kwargs.items()
            for item in items
        ]

    def sample(self, n=1024, clean=True):
        """
            Samples a given number of points

            Parameters
            ----------
                n: int [default=1024]
                    The number of points ot sample
                clean: bool [default=True]
                    When true, the tempory file are clean.
            
            Returns
            -------
                np array
                    The samples
        """
        outfile = os.path.join(__UTK__WDIR__, uuid.uuid4().hex + ".dat")
        points = self.sample_to(outfile, n)

        if clean:
            os.remove(outfile)
        return points

    def sample_to(self, outfile, n=1024):
        """
            Sample points to a file and return its content

            Parameters
            ----------
                outfile: str
                    The file to write to
                n: int [default=1024]
                    The number of samples

            Returns
            -------
                np array like
                    The samples
        """
        args = [
        os.path.join(get_samplers_dir(), self.exename),
            "-o", str(outfile), 
            "-n", str(n), 
            "-m", str(1)
        ] + get_silence_args() + self.args
        subprocess.run(args)
        
        reader = PointReader(n, self.d)
        points = reader.read(outfile)
        return points

class Discrepancy:
    """
        Interface to UTK Sampler
        
        This class encapsulate details to run a sampler of the utk libary

        Parameters
        ----------
            name: str
                The name of the discrepancy
            d: int
                The dimension of the point generated by the sampler
            index: str [default='d']
                Prefix to the sample name (either 'i' or 'd')
            **kwargs:
                Additionnal information for the discrepancy
    """
    def __init__(self, name, d, index='d', **kwargs):
        self.name = name
        self.d = d
        self.exename = f"{name}_fromfile_{d}d{index}"
        self.args = [
            str(item)
            for items in kwargs.items()
            for item in items
        ]

    def compute(self, points, s=-1, clean=True):
        """
            Compute the discrepancy of a point set

            Parameters
            ----------
                points: np array like
                    The point to compute the discrepancy of
                s: int [default=-1]
                    The number of point to take in the samples. 
                    When -1, all points are taken
                clean: bool [default=True]
                    When true, the tempory file are clean.

            Returns
            -------
                list
                    The computed discrepancy metrics
        """
        tmpfile = os.path.join(__UTK__WDIR__, uuid.uuid4().hex + ".dat")
        writer = PointWriter()
        writer.write(tmpfile, points)

        result = self.compute_from_file(tmpfile, s, clean)

        if clean:
            os.remove(tmpfile)
        return result

    def compute_from_file(self, input, s=-1, clean=True):
        """
            Compute the discrepancy of a file

            Parameters
            ----------
                input: str
                    The path to the file containing the points.
                s: int [default=-1]
                    The number of point to take in the samples. 
                    When -1, all points are taken
                clean: bool [default=True]
                    When true, the tempory file are clean.

            Returns
            -------
                list
                    The computed discrepancy metrics
        """
        outfile = os.path.join(__UTK__WDIR__, uuid.uuid4().hex + ".dat")
        discrepancy = self.compute_to(outfile, input, s)
        
        if clean:
            os.remove(outfile)
        return discrepancy

    def compute_to(self, outfile, input, s=-1):
        """
            Compute the discrepancy of a file to another

            Parameters
            ----------
                outfile: str:
                    The path to the file to write to. 
                input: str
                    The path to the file containing the points.
                s: int [default=-1]
                    The number of point to take in the samples. 
                    When -1, all points are taken
                clean: bool [default=True]
                    When true, the tempory file are clean.

            Returns
            -------
                list
                    The computed discrepancy metrics
        """
        args = [
            os.path.join(get_discrepancy_dir(), self.exename), 
            "-i", input, 
            "-o", outfile
        ]
        if s > -1:
            args = args + ["-s", str(s)]
        args = args + get_silence_args()  + self.args
        subprocess.run(args)    

        reader = DiscrepancyReader()
        results = reader.read(outfile)
        return results    

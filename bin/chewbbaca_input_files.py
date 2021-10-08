import argparse
import base_juno_pipeline.helper_functions
from os import system
import pathlib
import subprocess
from yaml import safe_load


class inputChewBBACA(base_juno_pipeline.helper_functions.JunoHelpers):
<<<<<<< HEAD
    '''
    Class to produce and enlist (in a dictionary) the parameters necessary to
    run chewBBACA for different genera. The samples can be run also by calling
    the runChewBBACA method
    '''
    def __init__(self, 
                sample_sheet='config/sample_sheet.yaml',
                output_dir='output/cgmlst/'):
        '''Constructor'''
        self.supported_genera = ['campylobacter', 'escherichia', 'listeria', 
                                'listeria_optional', 'salmonella','shigella', 
                                'yersinia']
=======
    """Class to produce and enlist (in a dictionary) the parameters necessary
    to run chewBBACA for different genera. The samples can be run also by calling
    the runChewBBACA method
    """

    def __init__(self, 
                best_hit_kmerfinder_files,
                sample_sheet='config/sample_sheet.yaml',
                output_dir='output/cgmlst/'):

        self.supported_genera = ['campylobacter', 'escherichia', 'listeria', 
                                'listeria_optional', 'salmonella','shigella', 
                                'yersinia']
        self.best_hit_kmerfinder_files = best_hit_kmerfinder_files
>>>>>>> fd6c11e597ac5d4c59d345ed50438c02b1b7aff3
        self.sample_sheet = pathlib.Path(sample_sheet)
        assert self.sample_sheet.is_file(), f'The provided sample sheet {str(self.sample_sheet)} does not exist.'
        self.output_dir = pathlib.Path(output_dir)


    def __read_sample_sheet(self):
        print("Reading sample sheet...\n")
        with open(self.sample_sheet) as sample_sheet_file:
            self.samples_dict = safe_load(sample_sheet_file)

    def __get_schemes_set(self):
        print(f'Getting list of all schemes needed to be run in this sample set...\n')
        self.__read_sample_sheet()
        schemes_set = set([self.samples_dict[sample]['cgmlst_scheme'] for sample in self.samples_dict])
        schemes_set = [scheme for scheme in schemes_set if scheme in self.supported_genera]
        second_schemes = [self.__get_second_scheme_name(scheme_name) for scheme_name in schemes_set]
        schemes_list = schemes_set + second_schemes
        schemes_list = [scheme_name for scheme_name in schemes_list if scheme_name is not None]
        self.schemes_list = schemes_list


    def __get_second_scheme_name(self, scheme):
        '''
        Some genera run two cgMLST schemes. This function gets the second 
        scheme name if existing
        '''
        if scheme == 'listeria':
            return 'listeria_optional'
        elif scheme == 'escherichia':
            return 'shigella'
        else:
            pass
        
    def __enlist_samples_per_scheme(self):
        print(f'Getting list of samples per scheme found...\n')
        self.__get_schemes_set()
        cgmlst_scheme_dict = {scheme_name:{'samples': []} for scheme_name in self.schemes_list}
        for scheme in self.schemes_list:
            samples_running_scheme = [sample for sample in self.samples_dict if self.samples_dict[sample]['cgmlst_scheme'] == scheme]
            cgmlst_scheme_dict[scheme]['samples'] = cgmlst_scheme_dict[scheme]['samples'] + samples_running_scheme
            second_scheme = self.__get_second_scheme_name(scheme)
            if second_scheme:
                cgmlst_scheme_dict[second_scheme]['samples'] = cgmlst_scheme_dict[second_scheme]['samples'] + samples_running_scheme
        return cgmlst_scheme_dict

    def make_file_with_samples_per_scheme(self):
        self.__read_sample_sheet()
        cgmlst_scheme_dict = self.__enlist_samples_per_scheme()
        for scheme in cgmlst_scheme_dict:
            scheme_file = self.output_dir.joinpath(scheme + '_samples.txt')
            with open(scheme_file, 'w') as file_:
                for sample in cgmlst_scheme_dict[scheme]['samples']:
                    assembly_file = self.samples_dict[sample]['assembly']
                    file_.write(assembly_file+'\n')
            cgmlst_scheme_dict[scheme]['scheme_file'] = str(scheme_file)
        print(f'Files with samples per scheme will be written in {self.output_dir} directory!\n')
        self.cgmlst_scheme_dict = cgmlst_scheme_dict
        return cgmlst_scheme_dict


if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser(description='run chewBBACA using the appropriate cgMLST scheme according to genus of sample(s)')
    argument_parser.add_argument('-s','--sample-sheet', type=pathlib.Path, 
                                default='config/sample_sheet.yaml',
                                help='Sample sheet (yaml file) containing a dictionary with the samples and at least one key:value pair assembly:file_path_to_assembly_file.\
                                    Example {sample1: {assembly: input_dir/sample1.fasta}}')
    argument_parser.add_argument('-o', '--output-dir', type=pathlib.Path, 
                                default='output/cgmlst',
                                help='Output directory for the chewBBACA results. A subfolder per genus/scheme will be created inside the output directory.')
    args = argument_parser.parse_args()
    chewbbaca_run = inputChewBBACA(sample_sheet=args.sample_sheet,
                                    output_dir=args.output_dir)
    chewbbaca_run.make_file_with_samples_per_scheme()

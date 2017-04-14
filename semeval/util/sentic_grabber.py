from senticnet.senticnet import Senticnet
import json

sn = Senticnet()

senticKeyNames = ["pleasantness", "attention", "sensitivity", "aptitude"]

def sentics2Tuple(sentics):
    """Converts sentics to tuple"""
    return (
        sentics[senticKeyNames[0]],
        sentics[senticKeyNames[1]],
        sentics[senticKeyNames[2]],
        sentics[senticKeyNames[3]])

def getSentics(wd):
    """Gets the sentics for a word as a dictionary"""
    concept_info = -1
    try:
        concept_info = sn.sentics(wd)
        return sentics2Tuple(concept_info)
    except KeyError:
        concept_info = {
            'pleasantness': '0',
            'attention': '0',
            'sensitivity': '0',
            'aptitude': '0'}
    return sentics2Tuple(concept_info)

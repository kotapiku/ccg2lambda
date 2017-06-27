# -*- coding: utf-8 -*-
#
#  Copyright 2017 Pascual Martinez-Gomez
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import print_function

from collections import OrderedDict
import json
import logging
import re
from subprocess import Popen
import subprocess
import sys

from nltk import Tree

from coq_analyzer import get_predicate_arguments
from knowledge import get_lexical_relations_from_preds
from normalization import denormalize_token
from theorem import is_theorem_defined
from theorem import is_theorem_error
from theorem import run_coq_script
from theorem import insert_axioms_in_coq_script
from tactics import get_tactics
from tree_tools import tree_or_string, tree_contains

def make_axioms_from_premises_and_conclusion(premises, conclusion, coq_output_lines=None):
    matching_premises = get_premises_that_match_conclusion_args(
        premises, conclusion)
    premise_preds = [premise.split()[2] for premise in matching_premises]
    conclusion_pred = conclusion.split()[0]
    pred_args = get_predicate_arguments(premises, conclusion)
    axioms = make_axioms_from_preds(premise_preds, conclusion_pred, pred_args)
    # print('Has axioms: {0}'.format(axioms), file=sys.stderr)
    failure_log = OrderedDict()
    if not axioms:
        failure_log = make_failure_log(
            conclusion_pred, premise_preds, conclusion, premises, coq_output_lines)
        # print(json.dumps(failure_log), file=sys.stderr)
    return axioms, failure_log


def make_axioms_from_preds(premise_preds, conclusion_pred, pred_args):
    axioms = set()
    linguistic_axioms = \
        get_lexical_relations_from_preds(
            premise_preds, conclusion_pred, pred_args)
    axioms.update(set(linguistic_axioms))
    # if not axioms:
    #   approx_axioms = GetApproxRelationsFromPreds(premise_preds, conclusion_pred)
    #   axioms.update(approx_axioms)
    return axioms


def try_abductions(theorem):
    assert len(theorem.variations) == 2, 'Got %d variations' % len(theorem.variations)
    theorem_master = theorem.variations[0]
    theorem_negated = theorem.variations[1]
    t_pos, t_neg = theorem_master, theorem_negated

    direct_proof_script = t_pos.coq_script
    reverse_proof_script = t_neg.coq_script
    axioms = t_pos.axioms.union(t_neg.axioms)
    current_axioms = t_pos.axioms.union(t_neg.axioms)
    failure_logs = []
    while True:
        abduction_theorem = try_abduction(
            t_pos, previous_axioms=current_axioms, expected='yes')
        current_axioms = axioms.union(abduction_theorem.axioms)
        reverse_proof_scripts = []
        if theorem_master.result == 'unknown':
            abduction_theorem = try_abduction(
                t_neg, previous_axioms=current_axioms, expected='no')
            theorem_master.variations.append(abduction_theorem)
            current_axioms.update(abduction_theorem.axioms)
        if len(axioms) == len(current_axioms) or theorem_master.result != 'unknown':
            break
        axioms = {a for a in current_axioms}
    return


def filter_wrong_axioms(axioms, coq_script):
    good_axioms = set()
    for axiom in axioms:
        new_coq_script = insert_axioms_in_coq_script(set([axiom]), coq_script)
        # We only need to check if there is a type mismatch, which should
        # be fast (2 secs. maximum).
        output_lines = run_coq_script(new_coq_script, timeout=2)
        if not is_theorem_error(output_lines):
            good_axioms.add(axiom)
    return good_axioms


def make_axioms_from_coq_analysis(failure_log):
    axioms = set()
    for subgoal in failure_log.get('other_sub-goals', []):
        conclusion_pred = subgoal.get('subgoal', '')
        premise_preds = subgoal.get('matching_premises', [])
        pred_args = get_predicate_arguments(
            subgoal.get('matching_raw_premises', []),
            subgoal.get('raw_subgoal', ''))
        subgoal_axioms = make_axioms_from_preds(
            premise_preds, conclusion_pred, pred_args)
        axioms.update(subgoal_axioms)
    return axioms

def try_abduction(theorem, previous_axioms=None, expected='yes'):
    if previous_axioms is None:
        previous_axioms = set()
    inference_result, failure_log = theorem.prove_debug(previous_axioms)
    if inference_result is True:
        abduction_theorem = theorem.copy(new_axioms=previous_axioms)
        return abduction_theorem

    axioms = make_axioms_from_coq_analysis(failure_log)
    axioms = filter_wrong_axioms(axioms, theorem.coq_script)
    axioms = axioms.union(previous_axioms)
    abduction_theorem = theorem.copy(new_axioms=axioms)
    abduction_theorem.prove_simple()
    return abduction_theorem


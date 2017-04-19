#!/usr/bin/env bash

root="$PWD"
dataRoot="/home/arya_b/Desktop/personal_projects/TobiTwitter/semeval16/data/subtask-A"

infile="$root/CHAR_DATA/semeval/train.chars.tsv"
testfile="$root/CHAR_DATA/semeval/test.chars.tsv"
#vocab="$dataRoot/ascii_vocab.pkl"
vocab="$root/CHAR_DATA/vocab.pkl"
labels="$root/CHAR_DATA/labels.pkl"

logdir="$root/debug_ascii"
mkdir -pv $logdir

THEANO_FLAGS=device=cpu,floatX=float32 python $root/semeval/lstm_chars.py \
--tweet-file $infile \
--vocab $vocab \
--log-path $logdir \
--test-file $testfile \
--batchsize "100" \
--nepochs "1" \
#--model-file "$root/bidir_lstm_ascii" \
--results-file "$logdir/bidir_ascii_results.txt" \
--label-file $labels


#!/usr/bin/env bash

root="$PWD"
dataRoot="/Users/aryan/Desktop/personal_projects/semeval16/CHAR_DATA"

infile="$dataRoot/semeval/train.chars.tsv"
testfile="$dataRoot/semeval/test.chars.tsv"
vocab="$dataRoot/semeval/train.chars.tsv.pkl"
labels="$dataRoot/labels.pkl"

logdir="$root/debug_ascii"
mkdir -pv $logdir

THEANO_FLAGS=device=cpu,floatX=float32 python $root/semeval/lstm_chars.py \
--tweet-file $infile \
--vocab $vocab \
--log-path $logdir \
--test-file $testfile \
--batchsize "100" \
--nepochs "1" \
--model-file "$root/bidir_lstm_ascii" \
--results-file "$logdir/bidir_ascii_results.txt" \
--label-file $labels


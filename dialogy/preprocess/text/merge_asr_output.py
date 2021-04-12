"""
We expect ASR transcripts to be the most common inputs to the system. Since there is a chance that we can improve the
performance by asking the ASR to provide more information in the form of multiple alternatives. The problem though, is
they can't be used as it is. Models that can operate on text data, need them to be vectorized. These vectors have
semantic significance, where different text inputs imply different vectors. If their semantic differences are modeled
well, we can expect these vectors to be similar or dissimilar just like the text that was used to create them.

The problem with transcripts is, there **will** be noise in the transcripts, since we asked for :code:`N` transcripts,
by definition, an ASR will provide N unique transcripts. The noise may in fact be inconsequential for downstream NLP
tasks, but we have noticed that there are certain inputs owing to audio artifacts or state of LMs tend to have a great
impact on the transcription.

This module will ship a simple concatenation strategy to address this problem. The NLP model should be expected to
handle documents (:code:`List[str]`) instead of single text. The plugin then will be able to produce a :code:`str` by
simply concatenation of each transcript.

This may not be very helpful, there is a :ref:`VotePlugin <vote_plugin>` under development so use it with caution. It may
help with precision at the cost of recall.
"""
from typing import Any, List

from dialogy.preprocess.text.normalize_utterance import normalize
from dialogy.types.plugin import (
    GetWorkflowUtteranceFn,
    PluginFn,
    UpdateWorkflowStringFn,
)
from dialogy.workflow import Workflow


# == merge_asr_output ==
def merge_asr_output(utterances: Any) -> str:
    """
    .. _merge_asr_output:

    Join ASR output to single string.

    This function provides a merging strategy for n-best ASR transcripts by
    joining each transcript, such that:

    - each sentence end is marked by " </s>" and,
    - sentence start marked by " <s>".

    The key "transcript" is expected in the ASR output, the value of which would be operated on
    by this function.

    .. ipython:: python

        from dialogy.preprocess import merge_asr_output

        utterances = ["This is a sentence", "That is a sentence"]
        merge_asr_output(utterances)

    :param utterances: A structure representing ASR output. We support only:

        1. :code:`List[str]`
        2. :code:`List[List[str]]`
        3. :code:`List[List[Dict[str, str]]]`
        4. :code:`List[Dict[str, str]]`

    :type utterances: Any
    :return: Concatenated string, separated by <s> and </s> at respective terminal positions of each sentence.
    :rtype: List[str]
    :raises: TypeError if transcript is missing in cases of :code:`List[List[Dict[str, str]]]` or
        :code:`List[Dict[str, str]]`.
    """
    try:
        flat_representation: List[str] = normalize(utterances)
        return "<s> " + " </s> <s> ".join(flat_representation) + " </s>"
    except TypeError as type_error:
        raise TypeError("`transcript` is expected in the ASR output.") from type_error


def merge_asr_output_plugin(
    access: GetWorkflowUtteranceFn, mutate: UpdateWorkflowStringFn
) -> PluginFn:
    """
    .. _merge_asr_output_plugin:

    Working details are covered in :ref:`merge_asr_output <merge_asr_output>`.

    :param access: A function that provides a :ref:`workflow<workflow>` and returns the ASR Utterance.
    :type access: GetWorkflowUtteranceFn
    :param mutate: A function that places the concat'd string into the :ref:`workflow<workflow>` as required.
    :type mutate: UpdateWorkflowStringFn
    :return: The plugin function.
    :rtype: Callable
    """

    def inner(workflow: Workflow) -> None:
        """
        Uses the `merge_asr_output` to build the plugin.

        Args:
        - workflow (Workflow):
        """
        merged_string = merge_asr_output(access(workflow))
        mutate(workflow, merged_string)

    return inner

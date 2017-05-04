_run-job_complete()
{
	local cur_word prev_word possibilities
	cur_word="${COMP_WORDS[COMP_CWORD]}"
	prev_word="${COMP_WORDS[COMP_CWORD-1]}"

	possibilities=`run-job -l`

	if [[ ${COMP_CWORD} == 1 ]]
	then
		possibilities+=" --job --list-jobs --status"
	fi

	# autocomplete for -j --job, or nothing
	if [[ ${prev_word} == "-j" || ${prev_word} == "--job" || ${COMP_CWORD} == 1 ]]
	then
		COMPREPLY=( $(compgen -W "${possibilities}" -- ${cur_word}) )
	else
		COMPREPLY=()
	fi
	return 0
}

complete -F _run-job_complete run-job

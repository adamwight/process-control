_run-job_complete()
{
	local cur_word prev_word possibilities
	cur_word="${COMP_WORDS[COMP_CWORD]}"
	prev_word="${COMP_WORDS[COMP_CWORD-1]}"

	if [[ ${COMP_CWORD} == 1 ]]
	then
		possibilities=`run-job -l`
		possibilities+=" --job --list-jobs --status --slow-start"
	elif [[ ${prev_word} == "-j" || ${prev_word} == "--job" ]]
	then
		possibilities=`run-job -l`
		possibilities+=" --slow-start"
	elif [[
		${prev_word} == "-l" ||
		${prev_word} == "--list-jobs" ||
		${prev_word} == "-s" ||
		${prev_word} == "--status"
	]]
	then
		possibilities="--only-running"
	else
		possibilities=""
	fi

	COMPREPLY=( $(compgen -W "${possibilities}" -- ${cur_word}) )

	return 0
}

complete -F _run-job_complete run-job

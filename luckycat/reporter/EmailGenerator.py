from tabulate import tabulate

class EmailGenerator:
    def process_stats_to_tabular_output(self, stats):
        output = ''
        for job in stats:
            tabulate_input = []
            tabulate_input.append(["Job", job['Job'], ''])
            for key,value in job['stats'].items():
                row = [key]
                for key, value in job['stats'][key].items():
                    row.append(key)
                    row.append(value)
                    tabulate_input.append(row)
                    row=['']
            output += tabulate(tabulate_input, headers='firstrow', tablefmt='fancy_grid') + '\n\n'
        return output



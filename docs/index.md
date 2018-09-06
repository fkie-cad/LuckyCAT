# Lucky CAT - Make Fuzzing Great Again!
Lucky CAT (*C*rash *A*ll the *T*hings) is a fuzzing management framework. Its ultimate goal is to automate the fuzzing workflow as much as possible. By doing that, it lets you focus on your target. For example, you can easily integrate your fuzzer, quickly setup a new fuzzing job or download the crashing test cases with only a couple of clicks. Born as a fork of the Nightmare Fuzzing Project, Lucky CAT brings fuzzing management to a new era. 
## Fuzz Job Management
Its main purpose is the managament of (distributed) fuzzing jobs. From the job creation to the inspection of crashes, Lucky CAT assists you during the whole fuzzing life cycle. Its ultimate goal is to automate the whole process as far as possible. 

Furthermore, Lucky CAT comes with a (basic) user management and lets you choose who views you fuzzing jobs and results.
## Easy Deployment 
It sets the gateway hurdle very low. Thanks to containerization (`docker` and `docker-compose`), its setup is easy, fast and hustle free. A basic installation should not require any tweaking of the configuration files. 
## Scalability
Lucky CAT comprises several (micro) services that run in their respective container. There are several ways how you can scale Lucky CAT. First, you can split the services across several servers. Second, you can run several fuzzer instances to speed up the fuzzing process. It does not matter whether or not your fuzzer uses an internal or an external mutation engine. 
## Easy Integration
Lucky CAT integrates with your other analysis tools. Use the RESTful interface to create jobs, get statistics or download crashes. 
## Responsive Web Interface
Lucky CAT comes with a clean and simple web interface. For example, you can create jobs, check exploitability, compare crashes and manage users. Have a look at some screenshots!
<table border="0px">
  <tr>
    <td><a href="https://raw.githubusercontent.com/fkie-cad/LuckyCAT/master/docs/screenshots/Lucky_CAT_job_creation.png"><img src="https://raw.githubusercontent.com/fkie-cad/LuckyCAT/master/docs/screenshots/Lucky_CAT_job_creation.png" alt="job creation" height="150px" /></a></td>
    <td><a href="https://raw.githubusercontent.com/fkie-cad/LuckyCAT/master/docs/screenshots/Lucky_CAT_results.png"><img src="https://raw.githubusercontent.com/fkie-cad/LuckyCAT/master/docs/screenshots/Lucky_CAT_results.png" alt="results" height="150px" /></a></td>
  </tr>
</table>
## Fast Command Line Client
Lucky CAT also comes with a fast and simple client for all the terminal ninja out there. Fuzzing job management at the tip of your fingers!
## Batteries Included!
Lucky CAT comes with batteries included: mutation engines, fuzzers and crash verifiers. Nevertheless, you may integrate your own fuzzing tools as well.
### Fuzzers
You need fuzzers in order to provoke crashes. They stress test the fuzzing target and check if it has crashed.
Lucky CAT comes with built-in fuzzers like the *elf_fuzzer* for fuzzing Linux/BSD ELF binaries or a minimalistic file fuzzer called *cfuzz*, which can be deployed on POSIX compatible devices like your average router. There are also plugins for other fuzzer projects: one plugin wraps *afl* for fuzzing x86/x64 targets on Linux and BSD and another plugin called *qemu_fuzzer* wraps *afl-other-arch* to fuzz binaries on all of the QEMU supported target architectures. 
### Mutation Engines
Lucky CAT allows fuzzer to have their own mutation engine (e.g. *afl*). However, many times you write a quick and simple fuzzer that does not come with its own mutation engine. Therefore, Lucky CAT mutates test cases for you. Mutated test cases are published via a queue from which multiple fuzzer instances can consume. This allows you to scale easily, just add more instances. As time of writing, Lucky CAT supports two fuzzing engines: *Radamsa* and */dev/urandom*.
### Crash Verifiers
What are all the crashes good for if you have to manually verify them and determine their exploitability? Therefore, Lucky CAT publishes them to registered verifier. They consume the crashing test cases and determine their exploitability for you. Currently, there are two verifiers included in Lucky CAT: a local and a remote exploitable verifier. Both utilize the GDB plugin `exploitable` in order to determine exploitability of a test case. The first does this locally. The second asks our remote C client (`rexploitablec`) to do so.
## Easy Fuzzer and Verifier Integration
Quickly integrate your fuzzers and verifiers into Lucky CAT. We provide several templates that make this as easy as counting until three. Templates are available for Python and C. Take a template as basis of your fuzzer/verifier. Don't forget to also have a look at the dummy_* examples. In a nutshell, it boils down to implementing a handful of functions. The templates will do the rest like sending the results to Lucky CAT.
# Contribute
There are many ways to contribute to Lucky CAT. These include, among others,

- bug fixes and general contriubtions to Lucky CAT (frontend, backend)
- enhancements, e.g. a new fuzzer plugin

No matter how you would like to contribute: If you have any question, do not hesitate to ask. 
# Contact
If you have any further questions, write a [mail](mailto:firmware-security@fkie.fraunhofer.de).
# Authors and Acknowledgment
FACT is developed by [Fraunhofer FKIE](https://www.fkie.fraunhofer.de).
Development is partly financed by [German Federal Office for Information Security (BSI)](https://www.bsi.bund.de).

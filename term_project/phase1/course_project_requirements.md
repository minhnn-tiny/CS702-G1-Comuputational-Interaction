# Term Project: Making an Interactive System — CS702 Computational Interaction (fetched from Notion, 8 Sep 2026)

## 💯 Overview
In this term project, you will select, implement, and evaluate an interaction technique or an interactive system from a Human-Computer Interaction (HCI) conference paper (e.g., UIST, IUI, UbiComp) published recently (preferably within the last three years). Working in groups of 2-3 students, you will replicate the interactive technology presented in the paper of your choice and evaluate its usability.
The project consists of a team building phase and four main phases with corresponding deliverables:
- Phase 0. Team Building (Week 3): Email the list of team members to us
- Phase 1. Proposal (Week 4, 5 points): Paper selection and implementation scope
- Phase 2. Prototype (Week 9, 5 points): Initial implementation and design documentation
- Phase 3. Presentation (Week 13, 30 points): In-class presentation of your work
- Phase 4. Final Report (Week 16, 60 points): Complete implementation and evaluation of your work

## 💯 Project Requirements
- Implementation and Evaluation. The final report must include both implementation and evaluation components. All intermediary deliverables, such as proposals and prototypes, should be developed with these final requirements in mind and built progressively toward the final report. Work from the earlier phases should guide what you deliver for the latter phase deliverables. For example, based on the scope of the work that you propose in Phase 1 and the feedback you get from the instructor (e.g., is the project scope too small or too big), you should determine what you prototype in Phase 2. In creating a prototype in Phase 2, you may find the interactive component is too easy/too hard to build. In such a case, you could re-adjust the scope of the work for the deliverables for Phase 3 and Phase 4.
- Work in a group.You must work in a group of 2–3 members. 
- Submit your work at the end of each phase. Each phase serves as a checkpoint in your project journey. For the first two checkpoints—Proposal and Prototype—submit concise reports. For the third checkpoint, share your presentation slides. The Final Report should be comprehensive, meeting the standards of a conference paper submission. See below for detailed deliverables for each project phase. All deadlines are in Singapore Time (SGT).

### Implementation
You must implement the interactive technology presented in your selected paper. The expected scope of implementation should be comparable to systems typically presented in HCI conference papers. These papers typically present systems with 2-3 key technical components. These components form an interactive system that enables users to accomplish specific tasks and achieve goals. Such papers often include evaluation with users, though some may not include formal evaluation.
You may select a paper from the main conference proceedings or other tracks like posters and demos. In case you choose to pick a paper from the main conference proceedings, please note that these papers typically present more complex systems that could be too ambitious for a semester-long project with 2-3 team members. In such a case, you should carefully scope the work that you will implement to replicate the work, rather than attempting to recreate the entire system.
Your implementation should follow the original design while remaining open to improvements. We encourage modifications that enhance the original technique, provided they align with the system's core objectives and can be completed within the project timeframe.

### Evaluation
Your evaluation should follow the method used in the original paper. Try to replicate their evaluation approach. However, when necessary (e.g., the extent of the evaluation is too large for a single semester project, the evaluation requires involvement of special user population that is hard to reach out), you may adjust the scope of the evaluation requirements. Where applicable, compare your findings with those from the original paper.
If the paper you chose lacks an evaluation component, conduct a user study that meets the minimum requirements:
- Include at least 12 participants
- Use qualitative methods, quantitative methods, or both

### Documentation and Presentation
You will document your work through written submissions and/or present it either in person or via video recordings at each project phase. See below for more details for deliverables for each project phase.

### Examples
Here are some examples to make the project requirements more concrete.
Consider an IUI 2024 Demo paper by Yamaguchi et al., "A Bicycle Navigation System for Analyzing the Comfort Level of the Cyclist" (‣). In this paper, the authors implement a few interactive components, including (i) a facial expression analysis system using a pre-trained DCNN model that detects five emotions (surprise, neutral, anger, happy, and sad), (ii) a road surface condition detection component that uses smartphone accelerometer data to identify rough and uneven surfaces, and (iii) a map-based interface for data collection and visualization that displays comfort levels using intuitive icons and color-coded markers for road conditions. The evaluation is relatively light-weight: they conducted a two-day field study with four participants (mean age = 41 years) who each rode bicycles for approximately 1.5 hours per day following system-recommended routes. The study collected 9,901 facial images, of which 2,533 were suitable for emotion analysis.
Another paper "NotebookGPT" by George and Dewan (‣), also from IUI 2024 Demo, implements (i) a mediated chat interface that filters out complete code blocks from GPT responses to encourage learning through explanation rather than code copying, (ii) a code context system that displays current code, standard output, and error messages from Jupyter Notebook cells, (iii) prompt generation tools that help students create effective queries by automatically formatting code snippets and generating instructor-style question templates, and (iv) a data collection interface that tracks student interactions and organizes data by student ID, course ID, and problem description. As a demo paper, the authors did not conduct any evaluation but suggested two potential evaluation directions: a controlled lab study to assess the effectiveness of their mediation approach and user interface, and an uncontrolled field study using tracked interaction data. For this kind of paper, I would like you to design your own evaluation plan and conduct it.
The amount of work represented by the above examples should be about right for your term project. If the paper that you selected describe something significantly more than this, you might want to consider scoping the amount of work.

## 📅 Phase 0: Team Member Selection (Week 1-3)
Email the list of team members to the instructor and TA by the end of the Week 3 lecture. This allows us to enter your team information into eLearn and set up the project assignment submission page. If you don’t, the instructor will assign you to a randomly formed group.

### Project Team (Fall 2026)

## 📅 Phase 1: Project Selection and Proposal 
(Week 1-4)
During this initial phase, you will form your project group, select your target paper, and prepare a proposal.

### Paper Selection Criteria
Keep in mind:
- The paper should be a work from an HCI-related conference (e.g., CHI, UIST, IUI, UbiComp) and published within the last three years. If you find a paper relevant to HCI but not from an HCI conference, we can discuss whether it is suitable. To explore published work, see recently hosted ACM HCI-related conference programs here: https://programs.sigchi.org/
- Your project must focus on interactive systems or novel interaction techniques. Other types of papers (e.g., purely empirical work) are not permitted for this term project.
- It is important to scope your work so you can complete the implementation by the end of the semester. If you’re not confident in your development skills, it is ok to select a paper from a demo or poster track that typically present simpler interactive systems and techniques with lighter-weight evaluation.
Once you’ve chosen a paper, identify its technical components and list them as bullet points. For example, in the bicycle navigation system described above, we can identify three distinct components: facial expression analysis, motion sensing, and map visualization. As a rule of thumb, you should be able to list the major components in about three bullet points—more may be too ambitious, and fewer may be too small in scope for the term project.

### Recommended Timeline
- Week 2: Form group and select target paper
- Week 3: Finalize the group members and let the instructors know the team members. Define the project scope
- Week 4: Submit project proposal by the end of Week 4

### Deliverables and Requirements
You must submit a written proposal. Your proposal should not be longer than 1000 words; keep it to one to two A4 page. It must include:
- List of team members (name and email address)
- Reference to the paper that your group selected
- Description of the paper's core contribution
- Architecture of the interactive technology described in the paper. Make a bullet point list of major components of the technology, together with a short description of what each component does.
- Implementation scope for your project. Carve out the interactive component, user interface and underlying system that supports interaction, that can be reimplemented within the project duration with the given resources.
- Evaluation plan. Describe what aspects of the interactive technology the authors evaluated. If a similar evaluation method seems feasible, you can replicate their study. Otherwise, describe any necessary modifications to the original paper’s methodology.

### Submission Instruction and Grading
- Submit the work via eLearn by the end of Week 4 (Friday 11:59PM)
- Grading will be based on clarity and completeness. Late submissions will incur point deductions.

## 📅 Phase 2: Creating a Prototype (Week 5-9)
Create an initial prototype based on your selected paper and the scope that you defined in your proposal. The prototype does not need to be fully functional at this stage. But your prototype should demonstrate the core interactive components you identified in Phase 1, even if some functionality is hard-coded or simulated with Wizard-of-Oz technique (‣). 
However, keep in mind that the prototype’s fidelity will impact your grade. Prototype fidelity refers to how closely your implementation matches the final intended system in terms of both appearance and functionality. For example, consider building a prototype of the bicycle navigation system. A almost fully functional prototype would include:
- A fully functional map interface showing the actual route
- Real-time display of basic comfort indicators
- Working accelerometer data collection
Acceptable simplifications might include:
- Using pre-recorded facial expressions instead of real-time analysis
- Simulating road condition data for specific test routes
- Implementing the system for a limited geographic area
If your prototype manifest the following characteristics similar to the following, you might need to put more effort in increasing your prototype’s fidelity:
- Static screenshots instead of interactive maps
- Random comfort indicators not based on any real data
- Missing core interactive features entirely

### Recommended Timeline
- Week 5-7: Work on creating the prototype
- (Week 8: Recess week)
- Week 9: Create a video and compile a written report

### Deliverables and Requirements
You must submit a short video demonstrating the interaction technique and a written report describing the implementation.
1. Video demonstration of your prototype's basic functionality. 
  - Submit an MP4 file no larger than 100MB. The video should be about 3 minutes long and no longer than 5 minutes.
  - The video should contain:
    - A short segment at the beginning that presents a list of team members and the reference to the original paper that you selected (5 to 10 seconds)
    - Explanation of the problem being solved. Brief introduction of the target users, users’ goal and tasks, and motivation of the work and role of the interaction technique (20 to 30 seconds)
    - Demo the interaction technique, showing how it (should) help the user complete tasks and achieve their goal. Show each implemented component in action and demonstrate typical user interactions.
    - In taking the video, ensure good lighting, clear audio, and steady camera work; test your demo beforehand; use screen recording for software interfaces; and add captions or text overlays for clarity if necessary.
1. Written report no longer than 1000 words (about one or two pages including figures) covering:
  - List of team members (name and email address)
  - Reference to the paper that your group selected
  - Current progress and implemented interactive components. Describe each implemented component, including: what features are fully implemented, what features are simplified or simulated, what features are planned but not yet implemented, any technical challenges encountered and how you addressed them.
  - Prototype fidelity assessment. Answer, “How closely does the interface match the intended final design?” “How realistic is the component's behavior?”, “How realistic is the data being used?”, “How well do components work together?” Again, your prototype does not have to be fully functional yet. But if the prototype’s fidelity is too low, you might need to spend more effort.
  - System architecture. Describe how the interactive system works. If it helps you in describing the system, provide a diagram showing the relationship between sytem components. Describe the current technical implementation of each component, frameworks being used, and any external APIs or services being utilized.
  - Implementation roadmap. Describe the remaining things to be implemented and timeline for completing them.
  - Updated evaluation plan (if changed from proposal)

### Submission Instruction and Grading
- Submit the deliverables through eLearn by the end of Week 9 (Friday 11:59PM).
- Grading will consider both documentation clarity and prototype fidelity. At this phase, video production quality will not affect your grade, but overly poor delivery (e.g., background audio and visual noise obscuring the contents) may negatively impact your grade. Late submission will incur point deductions.

## 📅 Phase 3: Implementation and Evaluation (Week 10-13)
During this phase, you will finalize your implementation and present your work to the class. This is a critical phase where your prototype evolves into a fully functional system. You should also begin your evaluation process during this period to gather preliminary results for your presentation and prepare for the more comprehensive evaluation in Phase 4.
Your implementation should now move beyond the prototype stage to demonstrate full functionality. Consider your system complete when:
- All core components work together seamlessly
- The user interface is polished and responsive
- Error handling is robust and graceful
- Performance is optimized for smooth operation
- Documentation is thorough and up-to-date
For example, if you implemented the bicycle navigation system in the example given above, your complete implementation should show:
- Reliable facial expression analysis with proper error handling
- Smooth integration of sensor data collection
- Responsive map updates and visualization
- Clear user feedback mechanisms
- Proper data storage and retrieval

### Recommended Timeline
- Week 10-12: Complete implementation
- Week 12: Begin user evaluation and prepare a presentation
- Week 13: Deliver in-class presentation

### Presentation Requirements
Your presentation should about 7-8 minutes. It should cover:
- Introduction (1-2 min). Explain the overview of selected paper and its contributions and the scope of implemented interactive components. Communicate who the target users are and what their goal and tasks are.
- Technical implementation (2-3 min). Walk through your system’s architecture and implementation.
- Live demo of the implementation (4-5 min). Before the presentation, test and practice your demo thoroughly on the presentation computer and prepare a backup video in case of technical issues.
- (Optional) Evaluation methodology and preliminary results if you have conducted a study
- Slides should preferably be made in Google Slides for easy sharing (but other formats are fine).

### Submission Instruction and Grading
- Submit the presentation slides (e.g., Google Slides, PowerPoint, PDF) before the class through eLearn.
- Presentations will be graded on clarity, live demo quality, and how well you communicate your target users' goals and how your implementation supports them.

## 📅 Phase 4: Final Report (Week 14-16)
During this final phase, you will document your implementation and conduct an evaluation of your interactive system. Your deliverables should demonstrate both technical features that enable interaction and evaluation of your system's effectiveness.

### Deliverables and Requirements
1. Written Report should be no longer than 3,000 words (about 4-6 pages including figures). The report should be more formal than the previous submissions; follow a format of typical computer science academic paper. Make sure to include:
  - Introduction. Begin by briefly introducing your project's context and goals. Explain the original paper's contribution, target users, and their needs.
  - Implementation details. Explain the scope of the work that you reimplemented and provide the technical overview of your interactive system. Describe your system architecture, explaining how different components work together to create the interactive experience.
  - User study method. Present your evaluation method with enough detail. Your text should answer, “What specific aspects of your implementation did you aim to evaluate?” “Who and how many did you recruit as study participants?” “How did you recruit them?” “What was the study procedure?”
  - Evaluation results and analyses. Present your findings clearly, using both quantitative and qualitative data to build a complete picture of your system's effectiveness. Start with an overview of your key findings, then support these with specific data and examples.
  - Discussion. Compare your results with the original paper's findings. Consider both similarities and differences. 
  - References. Include references if there are any. They will not count toward the page length limit.
1. Supporting Materials:
  - Short demo video. Create a one to two-minute video that demonstrates your system in action through realistic usage scenarios, showing user interactions while providing clear narration or captions to guide viewers through what they're seeing.
  - Complete source code. Include a clear README file explaining setup and usage.

### Submission Instruction and Grading
- Submit the deliverables through eLearn by the end of Week 16 (Friday 11:59PM).
- Final reports will be evaluated based on:
  - Technical implementation quality and sophistication
  - Evaluation methodology and execution
  - Documentation completeness and clarity
  - Quality of the demo video

<p align="center">
  <img src="Miscellaneous/Homepage Title image/首页抬头用图.PNG" alt="RWAI Arena" width="100%">
</p>

<p align="center">
  <a href="https://realworld-ai.io/en"><img alt="Website" src="https://img.shields.io/badge/🔗_Website-0088FF?style=flat-square&logoColor=white"></a>
  <a href="https://github.com/THU-ZJAI/Real-World-AI_Source"><img alt="GitHub" src="https://img.shields.io/badge/GitHub-Real--World--AI-181717?style=flat-square&logo=github"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-32CD32?style=flat-square"></a>
</p>

<p align="center">
  <a href="./README_zh.md"><b>简体中文</b></a> · <a href="./README.md"><b>English</b></a>
</p>

<p align="center"><b>Real-World AI Arena: Best AI Practice for Real-World Tasks</b><br><i>AI in Practice, Who is the Best?</i></p>

---

### Introduction

* **Real-World AI (RWAI)** is an **open-source project** dedicated to finding the **best AI practices for real-world scenarios**, answering two questions:
  * **How can I solve my scenario's problem with AI, and how can I quickly validate the results?**
  * **What is the best / most suitable solution for me?**
* Through the **Arena** model, we evaluate and recognize the **best practice (SOTA)** for each real-world scenario, leveraging the open-source community and open ecosystem to **accelerate AI adoption across industries**.
* The project is currently in beta. Feedback and suggestions are welcome :)

---

### Quick Start

We collect best practices for common **AI application categories** in real-world scenarios, including:

* **Service**: Professional Q&A, intelligent navigation, etc.
* **Management**: Business dashboard generation, KPI forecasting & optimization, etc.
* **Marketing**: Copywriting, poster design, etc.
* **Risk Control**: Core risk information extraction (e.g., financial reports), anomaly detection, etc.
* **Operations**: Digital employee setup, research report writing, etc.

We also organize solutions by **industry domains**, including but not limited to:

* Finance
* Energy & Chemicals
* Education
* Smart City
* R&D, etc.

Quick navigation for each module:

* [Official Site](https://realworld-ai.io/en/)
* [Website Source (Real-World-AI)](https://github.com/THU-ZJAI/Real-World-AI): Source code for the project website
* [Resource Navigation (Real-World-AI_Source)](https://github.com/THU-ZJAI/Real-World-AI_Source): This repository
  * [Best Practice Repository (SOTA)](SOTA%20Repository/): Sub-directory of this repo, storing resources (code, data, knowledge docs) for current and archived arena solutions
  * [Templates](Template/): Sub-directory of this repo, storing reference templates for various documents used in arena solutions
  * [MCP](MCP/): Sub-directory of this repo, storing MCPs used in arena solutions
  * [Miscellaneous](Miscellaneous/): Sub-directory of this repo, storing various materials including images and icons

---

### Best Practice Arena

We use the **Arena** model to evaluate best practices for each specific scenario. Each Arena represents a **real-world AI application challenge,** such as "Build a business dashboard and website demo within two days."

Based on real-world requirements and feedback, we continuously seek and recognize the "Champion" for each scenario—the **best practice (SOTA)**.

Details and rankings for each arena can be found on the [project website](https://realworld-ai.io/en/arena/).

If you would like to share your own best practice and contribute to the open-source AI solution community, please visit [Submit & Feedback](https://realworld-ai.io/en/about/).

---

### FAQ

**Q: What is Real-World AI?**

Real-World AI is an academic open-source project focused on **real-world AI adoption**. We share best-practice cases for solving real-world AI adoption problems through open-source code, documentation, and related resources.

The project is currently in internal beta. Feedback and suggestions are welcome :)

---

**Q: What is the Arena? Why evaluate best practices through "Arenas"?**

Two of the most common questions in AI adoption are:

* **How can I solve my scenario's problem with AI, and how can I quickly validate the results?**
* **What is the best / most suitable solution for me?**

We treat common real-world scenarios as "Arenas," continuously searching for best practices (SOTA) and crowning "Champions" for specific scenarios amid ever-evolving AI technologies. Through "**Tsinghua Curation**", we reduce the cost of **technology selection and trial-and-error**.

Real-world AI adoption criteria are complex; unlike academic benchmarks, there is no absolute score, so we do not rank—we only recognize best practices through comprehensive evaluation. Due to different deployment environments, a single arena may have multiple champions, such as an on-premise version and a cloud-service version.

---

**Q: What problem does Real-World AI solve? How is it different from GitHub, Hugging Face, and other open-source communities?**

The current AI open-source ecosystem is rich with code and experience sharing. However, real-world AI adoption is a complex and massive engineering effort. The core challenge lies in **human-AI interaction and practice**, including:

* Guiding and refining business requirements
* Injecting expert knowledge
* Designing technical solutions
* Operational workflows

Therefore, AI technology and code alone are not enough. **Talk is cheap, code is not enough, PRACTICE is all we need.**

We model and restore the **Human-in-the-Loop (HITL) system** in AI adoption, ensuring solutions are **verifiable, practical, and reproducible,** bridging the "**last mile**" of AI adoption. From an academic perspective, Real-World AI aims to work with the community on modelling real-world human-AI interactions (Modelling of Real-World HI-AI Interactions) and task datasets (Task Set), ultimately achieving intelligent real-world AI practice generation (NL2Practice).

A perhaps imperfect analogy: we are trying to build an ImageNet for real-world human-AI interaction. If we can accumulate enough real-world human-AI interaction data, perhaps we will be one step closer to building a "world model" piece by piece.

---

**Q: What resources can I get from Real-World AI?**

You can learn about, participate in, and share best-practice solutions for various real-world scenarios based on the latest AI technologies.

---

**Q: Who are the users of Real-World AI? Can non-programmers use it?**

Real-World AI is designed to help as many people involved in AI adoption as possible and invite them to co-build.

* **Decision-makers** can learn about the latest technology trends and real-world industry cases.
* **Business experts** can learn, reference, and practice the full AI adoption workflow in their own industries.
* **Developers** can learn and replicate the actual effects and best cases of applying the latest technologies in different scenarios.

Even without algorithm knowledge or coding skills, you can find many low-barrier, low-/no-code practice solutions. Each solution notes the skills and knowledge required for different user roles to help you understand how to quickly build an AI solution for your team.

In addition, these solutions also cover steps that business, product, and other teams can reference, helping you practice the full process of taking a project from "idea" to "demo" to "approval" and "implementation."

---

**Q: How do you define and evaluate "best practice"?**

As a team with long-term experience in industrial AI practice, we believe that the best practice for real-world AI should start from the goals of the real-world scenario, clearly defining the value AI adoption can bring to the industry—for example: safety and compliance, organizational fit, and system fit as basic requirements, as well as business effectiveness, implementation cost, and implementation cycle as effectiveness metrics.

In industrial AI practice, we select representative and generalizable scenarios with clear interfaces to common systems, define business-effectiveness metrics for the scenario, and search for best practices. In different practices, we evaluate each metric through an open and verifiable process. As AGI evolves, we will increasingly try to use AI to solve this problem—and our current work is valuable data accumulation for future NL2Solution.

Industrial AI application scenarios are long-tailed enough that their best practices differ from the single measurable metric SOTA in the academic sense. Industrial SOTA must be validated through practice in the industry, prioritizing practicality and stability over novelty. Therefore, in the early stages, we invite industry partner experts to test, select, and validate best practices with us, acting as a "referee" that is not absolutely correct but strives to be professional, fair, and grounded.

---

**Q: I want to contribute to Real-World AI. How can I get involved?**

There are currently three ways to collaborate with us:

1. Submit your work. See [Submit & Feedback](https://realworld-ai.io/en/about/) for details.
2. If you have highly customized needs or a desire for deep collaboration, please [contact us](https://realworld-ai.io/en/about/).
3. Submit feedback and suggestions. See [contact us](https://realworld-ai.io/en/about/) for details.

---

### Partners

The following organizations provide application scenarios, technical support, and co-creation. We welcome more enterprises, universities, and organizations to join. Please [contact us](https://realworld-ai.io/en/about/).

<p align="center">
  <img src="Miscellaneous/Partners logo/浙江清华长三院.png" height="100" alt="浙江清华长三角研究院">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/盛虹集团.png" height="80" alt="盛虹集团">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/BISHENG.png" height="75" alt="BISHENG">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/中国平安.png" height="80" alt="中国平安">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/中小银行联盟.png" height="85" alt="中小银行联盟">
</p>

<p align="center">
  <img src="Miscellaneous/Partners logo/中国南方电网.png" height="80" alt="中国南方电网">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/珠科数智.png" height="135" alt="珠科数智">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/OxValue.AI.png" height="100" alt="OxValue.AI">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/牛津大学高等研究院(苏州).png" height="130" alt="牛津大学高等研究院(苏州)">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/CICAS.png" height="100" alt="CICAS">&nbsp;&nbsp;
  <img src="Miscellaneous/Partners logo/智向寰宇.jpg" height="160" alt="智向寰宇">
</p>


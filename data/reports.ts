import mockData from "../mock_report.json";

class Project {
  title: string;
  categories: CategorySpent[];

  constructor(title: string, categories: CategorySpent[]) {
    this.title = title;
    this.categories = categories;
  }
}

class CategorySpent {
  title: string;
  spent: number;

  constructor(title: string, spent: number) {
    this.title = title;
    this.spent = spent;
  }
}

const categoriesDuplicated = mockData.projects.flatMap((project) => {
  return project.categories.map((category) => {
    return new CategorySpent(category.title, category.spent);
  });
});

const categoryTitleSet = new Set<string>(
  categoriesDuplicated.map((category) => category.title)
);
const categoryTitles = Array.from(categoryTitleSet);

const reports = mockData.projects.map((project) => {
  const categorySpents = categoryTitles.map((targetCategory) => {
    const spent = project.categories
      .filter((category) => category.title === targetCategory)
      .map((category) => category.spent)
      .reduce((prev, current) => prev + current, 0.0);
    return new CategorySpent(targetCategory, spent);
  });
  return new Project(project.title, categorySpents);
});

const report_plots = reports.map((project) => {
  const project_plots: any = {
    name: project.title,
  };

  project.categories.forEach((category) => {
    project_plots[category.title] = category.spent;
  });

  return project_plots;
});

const colors = ["#8884d8", "#82ca9d", "#ffc658", "#fccde2", "#fc5c9c"];
const categoryLabels = categoryTitles.map((category, index) => {
  return {
    title: category,
    color: colors[index],
  };
});

export const data = report_plots;
export const categories = categoryLabels;

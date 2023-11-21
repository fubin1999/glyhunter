# GlyHunter

## 安装

移动到 glyhunter 目录（包含pyproject.toml的目录）。
```shell
cd path/to/glyhunter
```

通过 pipx 安装。
```shell
pipx install .
```

如果之前已经安装过，需要覆盖安装新版本，请使用 --force 选项。
```shell
pipx install . --force
```

## 初次使用

初次使用请初始化。
```shell
glyhunter init
```

该命令会在用户目录下创建一个 .glyhunter 文件夹，其中包含配置文件 config.yaml 和默认的糖库。

重新安装后不需要再次初始化。如果想要重新初始化，可以使用 `glyhunter init --force` 命令。

## 使用

### 概述

用法: glyhunter COMMAND [ARGS, OPTIONS]...

Commands:

  - config: View and update GlyHunter configuration.
  - db: View and update GlyHunter database.
  - init: Initialize GlyHunter.
  - run: Run the GlyHunter workflow.

### 运行 GlyHunter

GlyHunter 可以直接处理 flexAnalysis 导出的 mass list（XLSX文件）。
```shell
glyhunter run data.xlsx
```

此处，data.xlsx 是 flexAnalysis 导出的 mass list 文件。
GlyHunter 会创建一个文件夹，名为 XLSX 文件的文件名（不包含后缀），加上 “_glyhunter_results”。
例如，在上面的例子中，GlyHunter 会创建一个名为 data_glyhunter_results 的文件夹。

文件夹中包括：

- 每个谱图的结果（原 XLSX 文件中的不同 sheet）会单独保存到一个 CSV 文件中，文件名为原 sheet 的名字。
- 三个 summary 表格，分别汇总了 intensity，area 和 sn。

### 修改全局配置文件

GlyHunter 的配置文件是一个 YAML 文件，名为 config.yaml，默认位于用户目录下的 .glyhunter 文件夹中。
如果要修改配置文件，请先使用 `glyhunter config --copy` 将配置文件复制到某一目录，然后再修改。

例如：
```shell
glyhunter config --copy /Users/username/Desktop
```

此时，/Users/username/Desktop 会出现一个名为 config.yaml 的配置文件副本。
请修改该文件并保存，具体的修改方法在配置文件中有详细说明。
修改完成后，运行 `glyhunter config --update` 命令更新 GlyHunter 的配置。

```shell
glyhunter config --update /Users/username/Desktop/config.yaml
```

### 修改全局糖库

GlyHunter 的糖库是 BYONIC 文件，位于用户目录下的 .glyhunter 文件夹中。
默认糖库为人血清N-糖库。如果要修改，请使用 `glyhunter db --update` 更新配置文件。
同样，可以用 `glyhunter db --copy` 命令保存当前糖库的副本。

BYONIC 文件的格式为：糖组成 % 糖质量，例如：
```
Hex(5)HexNAc(2) % 2039.742
```

注意，% 后面的质量会被 GlyHunter 忽略，因为 GlyHunter 会自己计算质量。

### 在运行时指定临时配置或糖库

可使用 `-c` 或 `-d` 命令在运行时临时指定配置文件或糖库。
例如：
```shell
glyhunter run data.xlsx -c /Users/username/Desktop/config.yaml -d /Users/username/Desktop/db.byonic
```

使用这种方法指定的配置文件或糖库只会在本次运行中生效，不会影响全局配置。

### 指定输出文件夹

GlyHunter 默认输出的文件夹是输入的 XLSX 的文件名加上 “_glyhunter_results”。
如果要修改输出的文件夹名称，使用 `-o` 或 `--output` 选项。

例如：
```shell
glyhunter run data.xlsx -o results
```

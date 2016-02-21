#!/usr/bin/groovy

package com.company;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import groovy.transform.*

import java.util.function.Function

import static java.util.stream.Collectors.toList;

public class Main2 {

    public static void main(String[] args) {


        List<Params> list = new ArrayList<>(200);
        for (String fileName : Arrays.asList("FB09-0")) {
            for (Float sigma : Arrays.asList(0.1f, 0.25f, 0.5f, 0.7f, 1f, 2f)) {
                list.add(new Params(sigma, 4, 0.5f, fileName));
            }
            for (float load = 0; load < 2; load += 0.1f) {
                list.add(new Params(0f, 4, load, fileName));
            }
            for (int d = 0; d < 10; d++) {
                list.add(new Params(0f, d, 0.9f, fileName));
            }
        }
        AtomicInteger count = new AtomicInteger(list.size());
        System.out.println("list size " + list.size());
        List<Runnable> runs = list.stream().map({ Params param ->
            Runnable task =
                    {
                        String command = "experiment.py --parse_swim ${param.file}.tsv --sigma $param.sigma 100 -dn $param.dovern --load $param.load";
                        println command
                        try {
                            int i = 1;
                            while (i != 0) {
                                String cmd = './' + command
                                     
                                Process p = Runtime.getRuntime().exec(cmd);
                                p.waitFor();
//                                BufferedReader br = new BufferedReader(new BufferedInputStream(p.getInputStream()));
                                System.out.println("Result code " + p.exitValue() + "  with " + param);
                                i = p.exitValue();
                                if (p.exitValue() != 0) {
                                    try {
                                        Thread.sleep(100000);
                                    } catch (Exception e) {
                                        e.printStackTrace();
                                    }
                                }
                            }
                            int andDecrement = count.decrementAndGet();
                            System.out.println("is left : " + andDecrement);
                        } catch (IOException e) {
                            e.printStackTrace();
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                    };
            return task;
        } as Function).collect(toList());
        ExecutorService executor = Executors.newFixedThreadPool(8);
        runs.each { executor.submit(it) };
        executor.shutdown();
        try {
            executor.awaitTermination(Long.MAX_VALUE, TimeUnit.NANOSECONDS);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }


    static class Params {
        String file;
        float sigma;
        int dovern;
        float load;

        public Params(float sigma, int dovern, float load, String file) {
            this.sigma = sigma;
            this.dovern = dovern;
            this.load = load;
            this.file = file;
        }

        @Override
        public String toString() {
            return "Params{" +
                    "sigma=" + sigma +
                    ", dovern=" + dovern +
                    ", load=" + load +
                    '}';
        }
    }
}

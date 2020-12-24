import { formatDate, getLocaleDateFormat, FormatWidth } from '@angular/common';
import { Component, EventEmitter, Input, Output, OnInit, OnDestroy, LOCALE_ID, Inject } from '@angular/core';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { NgbDateStruct } from '@ng-bootstrap/ng-bootstrap';
import { DateMaskFormatPipe } from 'src/app/pipes/date-mask-format.pipe';
import { DatePlaceholderFormatPipe } from 'src/app/pipes/date-placeholder-format.pipe';
import { DateDeformatPipe } from 'src/app/pipes/date-deformat.pipe';

export interface DateSelection {
  before?: string
  after?: string
}

const FILTER_LAST_7_DAYS = 0
const FILTER_LAST_MONTH = 1
const FILTER_LAST_3_MONTHS = 2
const FILTER_LAST_YEAR = 3

@Component({
  selector: 'app-filter-dropdown-date',
  templateUrl: './filter-dropdown-date.component.html',
  styleUrls: ['./filter-dropdown-date.component.scss']
})
export class FilterDropdownDateComponent implements OnInit, OnDestroy {

  quickFilters = [
    {id: FILTER_LAST_7_DAYS, name: "Last 7 days"},
    {id: FILTER_LAST_MONTH, name: "Last month"},
    {id: FILTER_LAST_3_MONTHS, name: "Last 3 months"},
    {id: FILTER_LAST_YEAR, name: "Last year"}
  ]

  constructor(
    @Inject(LOCALE_ID) private locale: string,
    private datePlaceholderFormatPipe: DatePlaceholderFormatPipe,
    private dateMaskFormatPipe: DateMaskFormatPipe,
    private dateDeformatPipe: DateDeformatPipe
  ) {
    this.locale = locale
    this.placeholder = datePlaceholderFormatPipe.transform(this.locale)
    this.mask = dateMaskFormatPipe.transform(this.placeholder)
  }

  placeholder: string = 'yyyy-mm-dd'
  mask: string = '0000-M0-d0'

  @Input()
  dateBefore: string

  @Input()
  dateAfter: string

  @Input()
  title: string

  @Output()
  datesSet = new EventEmitter<DateSelection>()

  private datesSetDebounce$ = new Subject()
  private sub: Subscription

  dpDateBeforeValue: NgbDateStruct
  dpDateAfterValue: NgbDateStruct

  ngOnInit() {
    this.sub = this.datesSetDebounce$.pipe(
      debounceTime(400)
    ).subscribe(() => {
      this.onChange()
    })
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe()
    }
  }

  setDateQuickFilter(qf: number) {
    this.dateBefore = null
    let date = new Date()
    switch (qf) {
      case FILTER_LAST_7_DAYS:
        date.setDate(date.getDate() - 7)
        break;

      case FILTER_LAST_MONTH:
        date.setMonth(date.getMonth() - 1)
        break;

      case FILTER_LAST_3_MONTHS:
        date.setMonth(date.getMonth() - 3)
        break

      case FILTER_LAST_YEAR:
        date.setFullYear(date.getFullYear() - 1)
        break

      }
    this.dateAfter = formatDate(date, 'shortDate', this.locale, "UTC")
    this.onChange()
  }

  onChange() {
    this.dpDateBeforeValue = this.dateBefore ? this.toNgbDate(this.dateDeformatPipe.transform(this.dateBefore, this.placeholder)) : null
    this.dpDateAfterValue = this.dateAfter ? this.toNgbDate(this.dateDeformatPipe.transform(this.dateAfter, this.placeholder)) : null

    this.datesSet.emit({
      after: this.dateAfter ? formatDate(this.dateDeformatPipe.transform(this.dateAfter, this.placeholder), 'yyyy-MM-dd', this.locale) : null,
      before: this.dateBefore ? formatDate(this.dateDeformatPipe.transform(this.dateBefore, this.placeholder), 'yyyy-MM-dd', this.locale) : null
    })
  }

  onChangeDebounce() {
    if (this.dateAfter?.length < (this.mask.length - 2)) this.dateAfter = null
    if (this.dateBefore?.length < (this.mask.length - 2)) this.dateBefore = null
    // dont fire on invalid dates using isNaN
    if (this.dateAfter && isNaN(this.dateDeformatPipe.transform(this.dateAfter, this.placeholder) as any)) this.dateAfter = null
    if (this.dateBefore && isNaN(this.dateDeformatPipe.transform(this.dateBefore, this.placeholder) as any)) this.dateBefore = null
    this.datesSetDebounce$.next()
  }

  dpAfterDateSelect(dateAfter: NgbDateStruct) {
    this.dateAfter = formatDate(dateAfter.year + '-' + dateAfter.month + '-' + dateAfter.day, 'shortDate', this.locale)
    this.onChange()
  }

  dpBeforeDateSelect(dateBefore: NgbDateStruct) {
    this.dateBefore = formatDate(dateBefore.year + '-' + dateBefore.month + '-' + dateBefore.day, 'shortDate', this.locale)
    this.onChange()
  }

  clearBefore() {
    this.dateBefore = null
    this.onChange()
  }

  clearAfter() {
    this.dateAfter = null
    this.onChange()
  }

  toNgbDate(date: Date): NgbDateStruct {
    if (!date) return null
    else {
      return {year: date.getUTCFullYear(), month: date.getUTCMonth() + 1, day: date.getUTCDate()}
    }
  }

}
